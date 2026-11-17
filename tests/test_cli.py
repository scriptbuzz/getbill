"""Run the whole interactive tool against a simulated S3 service provided by moto.

The source folder holds a synthetic CUR 2.0 file with big data and Amazon Bedrock lines,
once as CSV and once as Parquet, plus a small plain CSV file.
"""

import io

import boto3
import pytest
from moto import mock_aws
from openpyxl import load_workbook

from getbill import cli
from getbill.aws import AuthError

CUR2 = "cur2-2026-10.csv"
CUR2_PARQUET = "cur2-export-00001.snappy.parquet"
CONFIG = """
[profile source]
region = us-east-1
aws_access_key_id = testing
aws_secret_access_key = testing

[profile dest]
region = eu-west-1
aws_access_key_id = testing
aws_secret_access_key = testing
"""


@pytest.fixture
def aws(tmp_path, monkeypatch, cur2_csv, cur2_parquet):
    config = tmp_path / "config"
    config.write_text(CONFIG)
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "none"))
    for name in ("AWS_PROFILE", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1", aws_access_key_id="testing", aws_secret_access_key="testing")
        s3.create_bucket(Bucket="data")
        s3.put_object(Bucket="data", Key="in/b.csv", Body=b"x\nhello\n")
        s3.put_object(Bucket="data", Key=f"in/{CUR2}", Body=cur2_csv)
        s3.put_object(Bucket="data", Key=f"in/{CUR2_PARQUET}", Body=cur2_parquet)
        s3.put_object(Bucket="data", Key="in/notes.txt", Body=b"ignored")
        eu = boto3.client("s3", region_name="eu-west-1", aws_access_key_id="testing", aws_secret_access_key="testing")
        eu.create_bucket(Bucket="partner", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"})
        yield s3, eu


def answer(monkeypatch, *answers):
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))


def read_sheet(client, bucket, key):
    body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
    return load_workbook(io.BytesIO(body)).active


def column(sheet, heading):
    headings = [cell.value for cell in sheet[1]]
    return headings.index(heading) + 1


def test_same_bucket_interactive_converts_cur2(aws, monkeypatch):
    s3, _ = aws
    # Profile 2 = "source"; bucket 1 = "data"; folder "in"; files "all";
    # destination mode 1 = same bucket; folder "out"; confirm.
    answer(monkeypatch, "2", "1", "in", "all", "1", "out", "")
    assert cli.main([]) == 0
    sheet = read_sheet(s3, "data", "out/cur2-2026-10.xlsx")
    assert sheet.max_row > 300  # 300 usage lines plus tax and credit lines.
    cost = sheet.cell(row=2, column=column(sheet, "line_item_unblended_cost")).value
    account = sheet.cell(row=2, column=column(sheet, "line_item_usage_account_id")).value
    assert isinstance(cost, float)
    assert isinstance(account, str) and len(account) == 12
    products = {sheet.cell(row=r, column=column(sheet, "line_item_product_code")).value for r in range(2, sheet.max_row + 1)}
    assert {"AmazonBedrock", "ElasticMapReduce", "AWSGlue", "AmazonAthena"} <= products
    assert s3.head_object(Bucket="data", Key="out/b.xlsx")
    # The Parquet file is listed and converted too, named without ".snappy.parquet".
    parquet_sheet = read_sheet(s3, "data", "out/cur2-export-00001.xlsx")
    assert isinstance(parquet_sheet.cell(row=2, column=column(parquet_sheet, "line_item_unblended_cost")).value, float)


def test_other_account_uses_second_profile_and_asks_on_existing_file(aws, monkeypatch):
    s3, eu = aws
    eu.put_object(Bucket="partner", Key="excel/cur2-2026-10.xlsx", Body=b"old")
    # Source profile 2, bucket 1, folder in, file 2 (the CUR 2.0 file) only; destination
    # mode 3 (other account), profile 1 = "dest", continue although moto reports the same
    # account, bucket 2 = "partner", folder "excel", confirm, then "t" to keep the old file
    # and add a timestamp.
    answer(monkeypatch, "2", "1", "in", "2", "3", "1", "y", "2", "excel", "y", "t")
    assert cli.main([]) == 0
    keys = [o["Key"] for o in eu.list_objects_v2(Bucket="partner")["Contents"]]
    assert "excel/cur2-2026-10.xlsx" in keys
    assert any(k.startswith("excel/cur2-2026-10_") and k.endswith(".xlsx") for k in keys)


def test_options_run_without_questions(aws, monkeypatch):
    s3, _ = aws
    answer(monkeypatch)  # Any question would raise StopIteration and fail the test.
    code = cli.main([
        "--source-profile", "source", "--source-bucket", "data", "--source-folder", "s3://data/in/",
        "--files", "b.csv", "--dest-mode", "same-bucket", "--dest-folder", "/", "--yes",
    ])
    assert code == 0
    assert read_sheet(s3, "data", "b.xlsx")["A2"].value == "hello"


def test_missing_bucket_is_reported(aws, monkeypatch):
    answer(monkeypatch)
    assert cli.main(["--source-profile", "source", "--source-bucket", "nope"]) == 1


# ---------------------------------------------------------------- more run scenarios

SOURCE = ["--source-profile", "source", "--source-bucket", "data", "--source-folder", "in"]
TO_OUT = ["--dest-mode", "same-bucket", "--dest-folder", "out", "--yes"]


def body(client, bucket, key) -> bytes:
    return client.get_object(Bucket=bucket, Key=key)["Body"].read()


def test_another_bucket_in_the_same_account(aws, monkeypatch):
    _, eu = aws
    answer(monkeypatch)
    code = cli.main(SOURCE + ["--files", "b.csv", "--dest-mode", "same-account", "--dest-bucket", "partner",
                              "--dest-folder", "excel", "--yes"])
    assert code == 0
    assert read_sheet(eu, "partner", "excel/b.xlsx")["A2"].value == "hello"


@pytest.mark.parametrize("policy, replaced", [("overwrite", True), ("skip", False)])
def test_existing_workbook_is_overwritten_or_skipped(aws, monkeypatch, capsys, policy, replaced):
    s3, _ = aws
    s3.put_object(Bucket="data", Key="out/b.xlsx", Body=b"old")
    answer(monkeypatch)
    assert cli.main(SOURCE + ["--files", "b.csv", "--on-exists", policy] + TO_OUT) == 0
    assert (body(s3, "data", "out/b.xlsx") != b"old") is replaced
    if not replaced:
        assert "Skipped. The existing Excel file was left unchanged." in capsys.readouterr().out


def test_one_answer_covers_every_existing_workbook(aws, monkeypatch):
    s3, _ = aws
    for key in ("out/b.xlsx", "out/cur2-2026-10.xlsx"):
        s3.put_object(Bucket="data", Key=key, Body=b"old")
    # Overwrite the first workbook, then use the same answer for the rest without being asked again.
    answer(monkeypatch, "o", "y")
    assert cli.main(SOURCE + ["--files", f"b.csv,{CUR2}"] + TO_OUT) == 0
    assert body(s3, "data", "out/b.xlsx") != b"old"
    assert body(s3, "data", "out/cur2-2026-10.xlsx") != b"old"


def test_unknown_existence_still_asks_before_uploading(aws, monkeypatch, capsys):
    s3, _ = aws
    # Without s3:ListBucket on the destination, S3 cannot say whether a workbook exists.
    monkeypatch.setattr(cli, "object_exists", lambda bucket, key: None)
    answer(monkeypatch, "t")
    assert cli.main(SOURCE + ["--files", "b.csv"] + TO_OUT) == 0
    assert "cannot check whether" in capsys.readouterr().out
    keys = [item["Key"] for item in s3.list_objects_v2(Bucket="data", Prefix="out/")["Contents"]]
    assert any(key.startswith("out/b_") and key.endswith(".xlsx") for key in keys)


def test_a_broken_file_fails_alone_and_the_run_exits_with_1(aws, monkeypatch, capsys):
    s3, _ = aws
    s3.put_object(Bucket="data", Key="in/broken.parquet", Body=b"this is not a parquet file")
    answer(monkeypatch)
    assert cli.main(SOURCE + ["--files", "broken.parquet,b.csv"] + TO_OUT) == 1
    out = capsys.readouterr().out
    assert "This file failed" in out
    assert "1 converted, 0 skipped, 1 failed." in out
    assert body(s3, "data", "out/b.xlsx")


def test_expired_sso_sign_in_can_be_retried(aws, monkeypatch, capsys):
    real_sign_in, calls = cli.sign_in, []

    def expires_once(profile):
        calls.append(profile)
        if len(calls) == 1:
            raise AuthError('The SSO sign-in for profile "source" has expired or has not been started.',
                            login_command="aws sso login --profile source")
        return real_sign_in(profile)

    monkeypatch.setattr(cli, "sign_in", expires_once)
    answer(monkeypatch, "r")
    assert cli.main(SOURCE + ["--files", "b.csv"] + TO_OUT) == 0
    assert calls == ["source", "source"]
    assert "aws sso login --profile source" in capsys.readouterr().out


def test_quitting_after_a_failed_sign_in_stops_the_run(aws, monkeypatch, capsys):
    def always_rejected(profile):
        raise AuthError('AWS rejected the credentials for profile "source" as invalid.')

    monkeypatch.setattr(cli, "sign_in", always_rejected)
    answer(monkeypatch, "q")
    assert cli.main(["--source-profile", "source"]) == 1
    assert "Stopped because signing in did not work." in capsys.readouterr().err


@pytest.mark.parametrize("extra, message", [
    (["--files", "nope.csv"], "These files are not in"),
    (["--source-folder", "empty"], "No CSV or Parquet files were found"),
])
def test_wrong_options_stop_with_a_clear_message(aws, monkeypatch, capsys, extra, message):
    answer(monkeypatch)
    options = ["--source-profile", "source", "--source-bucket", "data", "--source-folder", "in"]
    if extra[0] == "--source-folder":
        options = options[:-2]
    assert cli.main(options + extra) == 1
    assert message in capsys.readouterr().err


def test_ctrl_c_stops_cleanly_with_exit_code_130(aws, monkeypatch):
    def interrupt(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", interrupt)
    assert cli.main([]) == 130
