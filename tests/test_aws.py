"""Signing in with AWS profiles, and the S3 checks, including the failure paths."""

import boto3
import botocore.exceptions as bce
import pytest
from botocore.exceptions import ClientError

from getbill.aws import AuthError, Bucket, normalize_folder, object_exists, sign_in

CONFIG = """
[profile keys]
region = us-east-1
aws_access_key_id = testing
aws_secret_access_key = testing

[profile sso]
region = us-east-1
sso_session = corp
sso_account_id = 111122223333
sso_role_name = Reader

[sso-session corp]
sso_start_url = https://example.awsapps.com/start
sso_region = us-east-1
"""


@pytest.fixture
def profiles(tmp_path, monkeypatch):
    """Point boto3 at a config file with one access-key profile and one SSO profile."""
    config = tmp_path / "config"
    config.write_text(CONFIG)
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "none"))
    for name in ("AWS_PROFILE", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)


class FailingSts:
    """Stands in for the STS client and fails the identity check with a chosen error."""

    def __init__(self, error):
        self.error = error

    def get_caller_identity(self):
        raise self.error


def sts_fails_with(monkeypatch, error):
    monkeypatch.setattr(boto3.session.Session, "client", lambda self, *args, **kwargs: FailingSts(error))


@pytest.mark.parametrize("typed, bucket, expected", [
    ("", "data", ""),
    ("/", "data", ""),
    ("reports/in", "data", "reports/in/"),
    ("/reports/in/", "data", "reports/in/"),
    ("s3://data/reports", "data", "reports/"),
    ("s3://data/", "data", ""),
    ("s3://other/reports", "data", "other/reports/"),
])
def test_folder_answers_become_s3_prefixes(typed, bucket, expected):
    assert normalize_folder(typed, bucket) == expected


def test_unknown_profile_is_reported(profiles):
    with pytest.raises(AuthError, match="is not in your AWS config files"):
        sign_in("missing")


def test_expired_sso_sign_in_gives_the_login_command(profiles, monkeypatch):
    sts_fails_with(monkeypatch, bce.UnauthorizedSSOTokenError())
    with pytest.raises(AuthError, match="has expired or has not been started") as failure:
        sign_in("sso")
    assert failure.value.login_command == "aws sso login --profile sso"


@pytest.mark.parametrize("code, message", [
    ("ExpiredToken", "have expired"),
    ("InvalidClientTokenId", "rejected the credentials"),
])
def test_rejected_access_keys_are_reported_without_an_sso_command(profiles, monkeypatch, code, message):
    sts_fails_with(monkeypatch, ClientError({"Error": {"Code": code, "Message": "test"}}, "GetCallerIdentity"))
    with pytest.raises(AuthError, match=message) as failure:
        sign_in("keys")
    assert failure.value.login_command is None


def test_missing_credentials_suggest_aws_configure(profiles, monkeypatch):
    sts_fails_with(monkeypatch, bce.NoCredentialsError())
    with pytest.raises(AuthError, match="has no credentials") as failure:
        sign_in("keys")
    assert failure.value.login_command == "aws configure --profile keys"


class FakeS3:
    """Stands in for the S3 client and answers or fails the existence check."""

    def __init__(self, error=None):
        self.error = error

    def head_object(self, **kwargs):
        if self.error:
            raise self.error
        return {}


def bucket_with(error=None) -> Bucket:
    return Bucket(name="reports", region="us-east-1", can_list=True, client=FakeS3(error))


def s3_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "test"}}, "HeadObject")


@pytest.mark.parametrize("code, expected", [
    (None, True),
    ("404", False),
    ("NoSuchKey", False),
    ("403", None),
    ("AccessDenied", None),
])
def test_existence_check_tells_yes_no_or_unknown(code, expected):
    error = s3_error(code) if code else None
    assert object_exists(bucket_with(error), "excel/report.xlsx") is expected


def test_existence_check_passes_on_unexpected_errors():
    with pytest.raises(ClientError):
        object_exists(bucket_with(s3_error("InternalError")), "excel/report.xlsx")
