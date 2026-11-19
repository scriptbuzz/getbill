"""getBill converts CSV and Parquet files stored in Amazon S3 into Excel workbooks."""

# The one place the version number is set. pyproject.toml reads it from here, and
# scripts/bump_version.py raises it and updates every place it is shown.
# A version such as 2.4.0a3 is an alpha release, shown as 2.4.0-alpha.3.
__version__ = "0.1.0a24"
