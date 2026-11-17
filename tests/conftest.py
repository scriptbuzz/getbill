"""Shared test helpers.

- load_script: loads a script from the scripts/ folder as a module, so tests can call its functions.
- cur2_csv and cur2_parquet: a small synthetic CUR 2.0 file made by scripts/generate_cur2_sample.py.
"""

import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(f"getbill_script_{name}", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def load_script():
    """Return a function that loads scripts/<name>.py as a fresh module."""
    return _load_script


@pytest.fixture(scope="session")
def cur2_csv(tmp_path_factory) -> bytes:
    """Return the bytes of a small CUR 2.0 file with 300 usage lines plus its tax and credit lines."""
    path = tmp_path_factory.mktemp("cur2") / "cur2.csv"
    _load_script("generate_cur2_sample").main(["--rows", "300", "--output", str(path)])
    return path.read_bytes()


@pytest.fixture(scope="session")
def cur2_parquet(tmp_path_factory) -> bytes:
    """Return the bytes of the same kind of CUR 2.0 file, written as Snappy-compressed Parquet."""
    pytest.importorskip("pyarrow")
    path = tmp_path_factory.mktemp("cur2") / "cur2.snappy.parquet"
    _load_script("generate_cur2_sample").main(["--rows", "300", "--output", str(path)])
    return path.read_bytes()
