"""getBill: an interactive command-line tool that converts CSV and Parquet files in S3 into Excel workbooks.

Every setting can be given as a command-line option. The tool asks a question in the
terminal for each setting that was not given.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from datetime import datetime
from typing import List, Optional

from botocore.exceptions import BotoCoreError, ClientError

from . import __version__
from .aws import (
    Account,
    AuthError,
    Bucket,
    BucketError,
    S3File,
    available_profiles,
    download,
    list_buckets,
    list_files,
    list_folders,
    normalize_folder,
    object_exists,
    open_bucket,
    sign_in,
    upload_xlsx,
)
from .converter import SUPPORTED_SUFFIXES, ConversionError, convert_to_xlsx, output_stem
from .prompts import ask_choice, ask_letter, ask_selection, ask_text, ask_yes_no

DEST_MODES = ("same-bucket", "same-account", "other-account")
ON_EXISTS = ("ask", "overwrite", "skip", "timestamp")
MAX_FOLDER_HINTS = 20


class Stop(Exception):
    """The tool cannot continue. The message says why."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="getbill",
        description=(
            "Convert CSV and Parquet files in an S3 folder into Excel workbooks and upload them to a "
            "destination folder. The destination can be in the same bucket, another bucket in "
            "the same AWS account, or a bucket in another AWS account. The tool asks for every "
            "setting that is not given as an option."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--source-profile", help="AWS profile that signs in to the source account.")
    parser.add_argument("--source-bucket", help="Bucket that holds the CSV and Parquet files.")
    parser.add_argument("--source-folder", help='Folder inside the source bucket. Use "/" for the top of the bucket.')
    parser.add_argument("--files", help='Comma-separated CSV or Parquet file names to convert, or "all".')
    parser.add_argument("--dest-mode", choices=DEST_MODES, help="Where the destination bucket is.")
    parser.add_argument("--dest-profile", help="AWS profile for the destination account (only for other-account).")
    parser.add_argument("--dest-bucket", help="Destination bucket (not used with same-bucket).")
    parser.add_argument("--dest-folder", help='Folder inside the destination bucket. Use "/" for the top of the bucket.')
    parser.add_argument(
        "--on-exists",
        choices=ON_EXISTS,
        default="ask",
        help="What to do when an Excel file with the same name already exists (default: ask).",
    )
    parser.add_argument("--yes", action="store_true", help="Skip the final confirmation before converting.")
    return parser


def heading(text: str) -> None:
    print(f"\n== {text} ==")


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


# ---------------------------------------------------------------- accounts and sign-in


def choose_account(purpose: str, preset: Optional[str]) -> Account:
    """Pick a profile, sign in with it, and offer a retry when the sign-in has expired."""
    profiles = available_profiles()
    profile = preset
    if not profile:
        if not profiles:
            raise Stop(
                "No AWS profiles were found in ~/.aws/config or ~/.aws/credentials.\n"
                "Create one with `aws configure sso` for SSO, or `aws configure` for access keys, "
                "and run this tool again."
            )
        preferred = os.environ.get("AWS_PROFILE")
        default = profiles.index(preferred) if preferred in profiles else (
            profiles.index("default") if "default" in profiles else 0
        )
        profile = profiles[ask_choice(f"Which AWS profile signs in to the {purpose} account?", profiles, default)]

    while True:
        try:
            account = sign_in(profile)
            print(f"  Signed in to AWS account {account.account_id} as {account.identity_arn}.")
            return account
        except AuthError as error:
            print(f"  {error}")
            if error.login_command:
                print(f"  To fix this, run this command in another terminal:\n    {error.login_command}")
            choices = {"r": "Try this profile again", "q": "Quit"}
            if profiles and not preset:
                choices = {"r": "Try this profile again", "p": "Pick a different profile", "q": "Quit"}
            answer = ask_letter("What would you like to do?", choices)
            if answer == "q":
                raise Stop("Stopped because signing in did not work.")
            if answer == "p":
                profile = profiles[ask_choice(f"Which AWS profile signs in to the {purpose} account?", profiles)]


# ---------------------------------------------------------------- buckets and folders


def choose_bucket(account: Account, purpose: str, preset: Optional[str], need_list: bool) -> Bucket:
    """Pick a bucket in the account and check that the profile can use it."""
    name = preset
    while True:
        if not name:
            buckets = list_buckets(account)
            if buckets:
                options = buckets + ["Type a bucket name that is not in this list"]
                index = ask_choice(f"Which bucket is the {purpose} bucket (account {account.account_id})?", options)
                name = buckets[index] if index < len(buckets) else ask_text(f"Name of the {purpose} bucket")
            else:
                print(f"  The profile is not allowed to list the buckets in account {account.account_id}.")
                name = ask_text(f"Name of the {purpose} bucket")
        name = normalize_folder(name).strip("/")  # Also accepts "s3://bucket".
        try:
            bucket = open_bucket(account, name)
        except BucketError as error:
            if preset:
                raise Stop(str(error))
            print(f"  {error}")
            name = None
            continue
        if not bucket.can_list:
            message = (
                f'  The profile "{account.profile}" is not allowed to list the contents of bucket '
                f'"{bucket.name}". It needs the s3:ListBucket permission on that bucket.'
            )
            if need_list:
                if preset:
                    raise Stop(message.strip())
                print(message)
                name = None
                continue
            print(message)
            print("  The tool will still try to upload, but it cannot check for existing files first.")
        print(f"  Using bucket {bucket.name} in region {bucket.region}.")
        return bucket


def show_folder_hints(bucket: Bucket) -> None:
    folders = list_folders(bucket)
    if not folders:
        print(f"  Bucket {bucket.name} has no folders at its top level.")
        return
    print(f"  Folders at the top of bucket {bucket.name}:")
    for folder in folders[:MAX_FOLDER_HINTS]:
        print(f"    {folder}")
    if len(folders) > MAX_FOLDER_HINTS:
        print(f"    ... and {len(folders) - MAX_FOLDER_HINTS} more.")


def choose_source_files(bucket: Bucket, folder_preset: Optional[str], files_preset: Optional[str]):
    """Pick the source folder and the CSV and Parquet files in it. Returns (folder, files)."""
    folder_text = folder_preset
    while True:
        if folder_text is None:
            show_folder_hints(bucket)
            folder_text = ask_text(
                "Source folder inside the bucket, for example reports/incoming (press Enter for the top of the bucket)",
                allow_empty=True,
            )
        folder = normalize_folder(folder_text, bucket.name)
        files = list_files(bucket, folder, SUPPORTED_SUFFIXES)
        location = f"s3://{bucket.name}/{folder}"
        if files:
            break
        if folder_preset is not None:
            raise Stop(f"No CSV or Parquet files were found directly inside {location}.")
        print(
            f"  No CSV or Parquet files were found directly inside {location}. "
            "Files in its subfolders are not included."
        )
        folder_text = None

    if files_preset:
        if files_preset.strip().lower() == "all":
            return folder, files
        wanted = [name.strip() for name in files_preset.split(",") if name.strip()]
        by_name = {file.name: file for file in files}
        missing = [name for name in wanted if name not in by_name]
        if missing:
            raise Stop(f"These files are not in {location}: {', '.join(missing)}")
        return folder, [by_name[name] for name in wanted]

    print(f"\n  CSV and Parquet files in {location}:")
    width = len(str(len(files)))
    for number, file in enumerate(files, start=1):
        changed = file.last_modified.strftime("%Y-%m-%d %H:%M")
        print(f"  {number:>{width}}. {file.name}  ({human_size(file.size)}, changed {changed})")
    indexes = ask_selection(
        'Which files should be converted? Type numbers such as 1,3,5-7, or "all"', len(files)
    )
    return folder, [files[i] for i in indexes]


def choose_destination(source_account: Account, source_bucket: Bucket, args):
    """Pick where the Excel files go. Returns (account, bucket, mode)."""
    mode = args.dest_mode
    if not mode:
        options = [
            f"The same bucket ({source_bucket.name}), in a different folder",
            f"Another bucket in the same AWS account ({source_account.account_id})",
            "A bucket in a different AWS account, signed in with a second profile",
        ]
        mode = DEST_MODES[ask_choice("Where should the Excel files be saved?", options)]

    if mode == "same-bucket":
        return source_account, source_bucket, mode

    if mode == "same-account":
        return source_account, choose_bucket(source_account, "destination", args.dest_bucket, need_list=False), mode

    heading("Destination account")
    account = choose_account("destination", args.dest_profile)
    if account.account_id == source_account.account_id:
        print(
            f"  This profile signs in to the same account ({account.account_id}) as the source profile."
        )
        if not args.yes and not ask_yes_no("Continue with this profile anyway?", default=True):
            raise Stop("Stopped so you can choose a different destination profile.")
    return account, choose_bucket(account, "destination", args.dest_bucket, need_list=False), mode


# ---------------------------------------------------------------- converting


def ask_on_exists(location: str, known: bool) -> str:
    if known:
        question = f"  {location} already exists. What should the tool do?"
    else:
        question = (
            f"  The tool cannot check whether {location} already exists, because the profile "
            "is not allowed to read that folder. What should the tool do?"
        )
    letter = ask_letter(
        question,
        {
            "o": "Overwrite the existing file",
            "s": "Skip this file",
            "t": "Keep the existing file and save the new one with the date and time added to its name",
        },
    )
    return {"o": "overwrite", "s": "skip", "t": "timestamp"}[letter]


def convert_files(files: List[S3File], source: Bucket, dest: Bucket, dest_folder: str, on_exists: str) -> int:
    """Convert every file and return how many failed."""
    converted = skipped = failed = 0
    policy = on_exists
    with tempfile.TemporaryDirectory(prefix="getbill-") as workdir:
        for number, file in enumerate(files, start=1):
            stem = output_stem(file.name)
            # Keep the file type in the local name, because the converter chooses its
            # reader from the name.
            suffix = next(s for s in SUPPORTED_SUFFIXES if file.name.lower().endswith(s))
            local_source = os.path.join(workdir, f"source{suffix}")
            local_xlsx = os.path.join(workdir, "result.xlsx")
            print(f"\n[{number}/{len(files)}] {file.name}")
            try:
                download(source, file.key, local_source)
                result = convert_to_xlsx(local_source, local_xlsx, sheet_name=stem)

                key = f"{dest_folder}{stem}.xlsx"
                exists = object_exists(dest, key)
                if exists is not False:
                    action = policy
                    if action == "ask":
                        action = ask_on_exists(f"s3://{dest.name}/{key}", known=exists is True)
                        remaining = len(files) - number
                        if remaining and ask_yes_no(
                            f"  Use the same answer for the other {remaining} file(s) if they also exist?",
                            default=False,
                        ):
                            policy = action
                    if action == "skip":
                        print("  Skipped. The existing Excel file was left unchanged.")
                        skipped += 1
                        continue
                    if action == "timestamp":
                        key = f"{dest_folder}{stem}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"

                upload_xlsx(dest, local_xlsx, key)
                print(
                    f"  Converted the {result.file_format} file ({result.rows:,} rows including the header, "
                    f"{result.columns:,} columns) and saved the workbook to s3://{dest.name}/{key}"
                )
                converted += 1
            except (ConversionError, ClientError, BotoCoreError, OSError) as error:
                print(f"  This file failed: {error}")
                failed += 1
            finally:
                for path in (local_source, local_xlsx):
                    if os.path.exists(path):
                        os.remove(path)

    heading("Result")
    print(f"  {converted} converted, {skipped} skipped, {failed} failed.")
    return failed


# ---------------------------------------------------------------- main flow


def run(args) -> int:
    print("getBill converts CSV and Parquet files in S3 into Excel workbooks. Press Ctrl+C at any time to stop.")

    heading("Source account")
    source_account = choose_account("source", args.source_profile)

    heading("Source bucket and files")
    source_bucket = choose_bucket(source_account, "source", args.source_bucket, need_list=True)
    source_folder, files = choose_source_files(source_bucket, args.source_folder, args.files)

    heading("Destination")
    dest_account, dest_bucket, mode = choose_destination(source_account, source_bucket, args)
    dest_text = args.dest_folder
    if dest_text is None:
        if dest_bucket.can_list:
            show_folder_hints(dest_bucket)
        dest_text = ask_text('Destination folder inside the bucket, for example reports/excel (type "/" for the top of the bucket)')
    dest_folder = normalize_folder(dest_text, dest_bucket.name)
    if dest_bucket is source_bucket and dest_folder == source_folder:
        print("  The destination folder is the same as the source folder. The Excel files will sit next to the source files.")

    heading("Summary")
    print(f"  Source:       s3://{source_bucket.name}/{source_folder}  (account {source_account.account_id}, profile {source_account.profile})")
    print(f"  Files:        {len(files)} file(s): {', '.join(f.name for f in files[:5])}{' ...' if len(files) > 5 else ''}")
    print(f"  Destination:  s3://{dest_bucket.name}/{dest_folder}  (account {dest_account.account_id}, profile {dest_account.profile})")
    if mode == "other-account":
        print("  The files are downloaded with the source profile and uploaded with the destination profile.")
    print("  The original CSV and Parquet files are not changed or deleted.")
    if not args.yes and not ask_yes_no("Start the conversion?", default=True):
        print("Stopped. Nothing was converted.")
        return 0

    failed = convert_files(files, source_bucket, dest_bucket, dest_folder, args.on_exists)
    return 1 if failed else 0


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except Stop as stop:
        print(f"\n{stop}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Files that were already uploaded stay in place.", file=sys.stderr)
        return 130
