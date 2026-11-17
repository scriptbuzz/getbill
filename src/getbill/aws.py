"""Sign-in to AWS through named profiles, and the S3 operations the tool needs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import boto3
import botocore.exceptions as bce
from botocore.exceptions import BotoCoreError, ClientError

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FALLBACK_REGION = "us-east-1"

# Errors botocore raises when an IAM Identity Center (SSO) sign-in is missing or expired.
# Older botocore versions do not define every one of them, so missing names are skipped.
_SSO_ERRORS: Tuple[type, ...] = tuple(
    getattr(bce, name)
    for name in ("SSOTokenLoadError", "UnauthorizedSSOTokenError", "TokenRetrievalError", "SSOError")
    if hasattr(bce, name)
)
_EXPIRED_CODES = {"ExpiredToken", "ExpiredTokenException", "RequestExpired"}
_INVALID_CODES = {"InvalidClientTokenId", "SignatureDoesNotMatch", "UnrecognizedClientException"}


class AuthError(Exception):
    """Signing in with a profile failed. login_command, when set, is the command that fixes it."""

    def __init__(self, message: str, login_command: Optional[str] = None):
        super().__init__(message)
        self.login_command = login_command


class BucketError(Exception):
    """A bucket does not exist or the profile is not allowed to use it."""


@dataclass
class Account:
    profile: str
    session: boto3.Session
    account_id: str
    identity_arn: str


@dataclass
class Bucket:
    name: str
    region: str
    can_list: bool
    client: object  # A boto3 S3 client created for the bucket's own region.


@dataclass
class S3File:
    key: str
    size: int
    last_modified: datetime

    @property
    def name(self) -> str:
        return self.key.rsplit("/", 1)[-1]


def available_profiles() -> List[str]:
    """Return the profile names found in ~/.aws/config and ~/.aws/credentials."""
    return sorted(boto3.Session().available_profiles)


def _is_sso_profile(session: boto3.Session) -> bool:
    try:
        config = session._session.get_scoped_config()  # botocore's view of this profile
    except BotoCoreError:
        return False
    return "sso_start_url" in config or "sso_session" in config


def sign_in(profile: str) -> Account:
    """Open a session for the profile and confirm the credentials work by calling STS."""
    login_command = f"aws sso login --profile {profile}"
    try:
        session = boto3.Session(profile_name=profile)
    except bce.ProfileNotFound:
        raise AuthError(f'The profile "{profile}" is not in your AWS config files.')

    sso = _is_sso_profile(session)
    try:
        sts = session.client("sts", region_name=session.region_name or FALLBACK_REGION)
        identity = sts.get_caller_identity()
    except _SSO_ERRORS:
        raise AuthError(
            f'The SSO sign-in for profile "{profile}" has expired or has not been started.',
            login_command=login_command,
        )
    except bce.NoCredentialsError:
        hint = login_command if sso else f"aws configure --profile {profile}"
        raise AuthError(f'The profile "{profile}" has no credentials.', login_command=hint)
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "")
        if code in _EXPIRED_CODES:
            raise AuthError(
                f'The credentials for profile "{profile}" have expired.',
                login_command=login_command if sso else None,
            )
        if code in _INVALID_CODES:
            raise AuthError(f'AWS rejected the credentials for profile "{profile}" as invalid.')
        raise AuthError(f'Signing in with profile "{profile}" failed: {error}')
    except BotoCoreError as error:
        raise AuthError(f'Signing in with profile "{profile}" failed: {error}')

    return Account(
        profile=profile,
        session=session,
        account_id=identity["Account"],
        identity_arn=identity["Arn"],
    )


def list_buckets(account: Account) -> Optional[List[str]]:
    """Return the account's bucket names, or None when the profile may not list buckets."""
    client = account.session.client("s3", region_name=account.session.region_name or FALLBACK_REGION)
    try:
        response = client.list_buckets()
    except (ClientError, BotoCoreError):
        return None
    return sorted(bucket["Name"] for bucket in response.get("Buckets", []))


def open_bucket(account: Account, name: str) -> Bucket:
    """Find the bucket's region and check access, then return a client for that region."""
    probe = account.session.client("s3", region_name=account.session.region_name or FALLBACK_REGION)
    try:
        response = probe.head_bucket(Bucket=name)
        headers = response["ResponseMetadata"].get("HTTPHeaders", {})
        can_list = True
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "")
        headers = error.response.get("ResponseMetadata", {}).get("HTTPHeaders", {})
        if code in ("404", "NoSuchBucket", "NotFound"):
            raise BucketError(f'The bucket "{name}" does not exist.')
        if code not in ("403", "AccessDenied", "Forbidden"):
            raise BucketError(f'The bucket "{name}" could not be checked: {error}')
        can_list = False
    except BotoCoreError as error:
        raise BucketError(f'The bucket "{name}" could not be checked: {error}')

    region = headers.get("x-amz-bucket-region") or account.session.region_name or FALLBACK_REGION
    client = account.session.client("s3", region_name=region)
    return Bucket(name=name, region=region, can_list=can_list, client=client)


def normalize_folder(text: str, bucket_name: str = "") -> str:
    """Turn what the user typed into an S3 key prefix: "" for the top of the bucket, else "a/b/".

    Accepts "reports/in", "/reports/in/" and "s3://my-bucket/reports/in".
    """
    folder = text.strip()
    if folder.lower().startswith("s3://"):
        folder = folder[5:]
        if bucket_name and folder.split("/", 1)[0] == bucket_name:
            folder = folder[len(bucket_name):]
    folder = folder.strip("/")
    return f"{folder}/" if folder else ""


def list_folders(bucket: Bucket, prefix: str = "") -> List[str]:
    """Return the folders directly under the prefix."""
    paginator = bucket.client.get_paginator("list_objects_v2")
    folders: List[str] = []
    for page in paginator.paginate(Bucket=bucket.name, Prefix=prefix, Delimiter="/"):
        folders.extend(item["Prefix"] for item in page.get("CommonPrefixes", []))
    return folders


def list_files(bucket: Bucket, folder: str, suffixes: Tuple[str, ...]) -> List[S3File]:
    """Return the files directly inside the folder whose names end with one of the suffixes.

    The comparison ignores upper and lower case. Subfolders are not searched.
    """
    paginator = bucket.client.get_paginator("list_objects_v2")
    files: List[S3File] = []
    for page in paginator.paginate(Bucket=bucket.name, Prefix=folder, Delimiter="/"):
        for item in page.get("Contents", []):
            if item["Key"].lower().endswith(suffixes):
                files.append(S3File(key=item["Key"], size=item["Size"], last_modified=item["LastModified"]))
    return sorted(files, key=lambda f: f.key)


def object_exists(bucket: Bucket, key: str) -> Optional[bool]:
    """Return True or False, or None when the profile is not allowed to check.

    Without the s3:ListBucket permission S3 answers "access denied" instead of
    "not found" for a missing file, so the answer is unknown.
    """
    try:
        bucket.client.head_object(Bucket=bucket.name, Key=key)
        return True
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey", "NotFound"):
            return False
        if code in ("403", "AccessDenied", "Forbidden"):
            return None
        raise


def download(bucket: Bucket, key: str, local_path: str) -> None:
    bucket.client.download_file(bucket.name, key, local_path)


def upload_xlsx(bucket: Bucket, local_path: str, key: str) -> None:
    """Upload the workbook. The bucket's default encryption setting applies to it."""
    bucket.client.upload_file(local_path, bucket.name, key, ExtraArgs={"ContentType": XLSX_CONTENT_TYPE})
