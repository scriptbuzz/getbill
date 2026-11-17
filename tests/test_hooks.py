"""The Git hooks: the secret check before each commit and the version check before each push.

Each test makes a throwaway Git repository that uses the hooks from .githooks.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parent.parent / ".githooks"
pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="Git is not installed")

# Built from two parts so that this test file itself passes the secret check. It is the example
# access key ID from the AWS documentation, not a real key.
EXAMPLE_KEY = "AKIA" + "IOSFODNN7EXAMPLE"
NO_COMMIT = "0" * 40


def git(repo, *args, check=True):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "tests@example.com")
    git(tmp_path, "config", "user.name", "Tests")
    git(tmp_path, "config", "core.hooksPath", str(HOOKS))
    return tmp_path


def commit(repo, name, text):
    (repo / name).write_text(text)
    git(repo, "add", "-f", name)
    return git(repo, "commit", "-q", "-m", f"Add {name}", check=False)


# ---------------------------------------------------------------- pre-commit: secrets

def test_a_clean_commit_passes(repo):
    assert commit(repo, "notes.txt", "Nothing secret here.\n").returncode == 0


def test_an_aws_key_is_blocked_and_never_printed(repo):
    result = commit(repo, "settings.py", f'access_key = "{EXAMPLE_KEY}"\n')
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "AWS access key ID" in output
    assert "[hidden]" in output
    assert EXAMPLE_KEY not in output


@pytest.mark.parametrize("name", ["server.pem", "deploy.key", ".env", "id_ed25519"])
def test_key_and_secret_files_are_blocked_even_when_forced(repo, name):
    result = commit(repo, name, "contents\n")
    assert result.returncode != 0
    assert name in result.stdout + result.stderr


def test_a_line_marked_as_a_false_alarm_passes(repo):
    text = f"The AWS documentation uses {EXAMPLE_KEY} as an example.  secret-scan: allow\n"
    assert commit(repo, "guide.md", text).returncode == 0


# ---------------------------------------------------------------- pre-push: version

def commit_version(repo, version):
    package = repo / "src" / "getbill"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(f'__version__ = "{version}"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"Version {version}")
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def pre_push(repo, local, remote):
    line = f"refs/heads/main {local} refs/heads/main {remote}\n"
    return subprocess.run(["sh", str(HOOKS / "pre-push")], cwd=repo, input=line, capture_output=True, text=True)


def test_a_push_without_a_new_version_is_refused(repo):
    on_github = commit_version(repo, "0.1.0a2")
    commit(repo, "change.txt", "A change without a version bump.\n")
    local = git(repo, "rev-parse", "HEAD").stdout.strip()
    result = pre_push(repo, local, on_github)
    assert result.returncode == 1
    assert "already at version 0.1.0a2" in result.stdout
    assert "scripts/bump_version.py" in result.stdout


def test_a_push_with_a_new_version_passes(repo):
    on_github = commit_version(repo, "0.1.0a2")
    local = commit_version(repo, "0.1.0a3")
    result = pre_push(repo, local, on_github)
    assert result.returncode == 0
    assert "0.1.0a2 becomes 0.1.0a3" in result.stdout


def test_the_first_push_of_a_branch_passes(repo):
    local = commit_version(repo, "0.1.0a1")
    assert pre_push(repo, local, NO_COMMIT).returncode == 0
