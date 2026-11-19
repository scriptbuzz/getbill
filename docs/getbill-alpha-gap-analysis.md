# getBill alpha: what the prototype does today

_Last modified: 2026-11-19 14:27 EST_

_Version: 0.1.0-alpha.23_

This note is for the engineering team. It records what the getBill alpha prototype can and cannot
do, so that its gaps can be compared with the product owner's answers in the
[requirements questionnaire](getbill-pipeline-questions.md).

The alpha is not a reference for the requirements. getBill will be built to match the answers,
whatever the alpha does today. When answers arrive, each row below either becomes work to do or is
dropped because nobody needs it.

## What the alpha does

| Area | What the alpha does | Related questions |
| --- | --- | --- |
| Use | A command-line tool that a person runs on their own computer. It asks its questions one at a time, or takes every answer as an option. | G3, G4, P8 |
| Sign-in | Signs in with AWS profiles, including IAM Identity Center (SSO). It shows the exact login command when an SSO session expires. | C1 |
| Source | Reads files directly inside one S3 folder that you choose. | S8 |
| Formats in | Reads plain CSV files, and Parquet files with Snappy compression. | S7 |
| Output | Writes one Excel workbook for each source file. The workbook has a bold, filtered, frozen header row, and column widths that fit the content. | G5, P1, P4 |
| Values | Keeps costs as numbers, account IDs as text, and Parquet dates as Excel dates in UTC. Tag maps become JSON text. Text that starts with `=` is stored as plain text. | P5, P6 |
| Destination | Uploads workbooks to the same bucket, another bucket, or a bucket in another AWS account that a second profile signs in to. | D2, D8 |
| Existing results | Asks whether to overwrite, skip, or keep both by adding the date and time to the name. | D7 |
| Failures | Reports a failed file, converts the others, and exits with code 1. | P10 |
| Quality | Has 123 automated tests that run on GitHub Actions on Python 3.9 and 3.12, with 91% code coverage. Every push raises the version number. | O5 |

## Known limitations

| # | Limitation | Related questions |
| --- | --- | --- |
| 1 | Cannot read gzip-compressed CSV files (`.csv.gz`), which is how AWS Data Exports writes CSV, or ZIP archives. Parquet with gzip or Zstandard compression is untested. | S7 |
| 2 | Does not search month subfolders, does not read the export's manifest file, and turns each part file into its own workbook. | S8, S9 |
| 3 | Stops a file that has more than 1,048,576 rows or 16,384 columns, instead of splitting or summarizing it. | P9, L1, L2 |
| 4 | Keeps a CSV number with more than 15 significant digits as text, so Excel leaves it out of sums. | L3 |
| 5 | Does not check Excel's limit of 32,767 characters in one cell, or that dates fall in Excel's range. | L5, L6 |
| 6 | Copies every line to every workbook. It cannot filter or split by account, cost center or tag. | D3 |
| 7 | Makes no summaries, totals, statements, charts, or other output formats. | G5, P1 |
| 8 | Does not rename or select columns, change prices, convert currency, or translate. | P3, P4, G6, G7 |
| 9 | Cannot detect a restated month or a changed export layout. | S11, Q4 |
| 10 | Does not reconcile totals with the source or with the AWS invoice. | Q1, Q2 |
| 11 | Sends no notices, receipts or failure alerts, and keeps no run log or audit record. | D6, R2, R3, C4 |
| 12 | Has no schedule and no automated deployment in AWS. | P8 |
| 13 | Does not archive, apply retention rules, or delete anything. | A1 to A5 |
| 14 | Copies each file to the computer while it converts it. A crash could leave that copy behind. | P12 |
| 15 | Has never been run against real AWS accounts or real billing exports. | O6 |
| 16 | Has not been tested with AWS GovCloud (US). When a profile names no AWS Region, getBill signs in through the standard `us-east-1` Region, which a GovCloud profile cannot use. | C11 |
| 17 | Does not use AWS's FIPS 140 validated endpoints, and does not check that the computer's own encryption libraries are FIPS validated. | C12 |
| 18 | Has no security controls mapped to any framework, such as NIST SP 800-53, NIST SP 800-171, FedRAMP or CMMC, and no system security plan. | C9, C10 |
| 19 | Ships no secure software development attestation, software bill of materials (SBOM), or vulnerability disclosure policy. | C13 |
| 20 | Has not been checked for accessibility. The workbooks and web pages have not been tested against Section 508. | C14 |
| 21 | Cannot limit who runs it or from where. Access depends entirely on each person's AWS permissions. | C15 |

<!-- document-footer -->
---

_Internal use only. Version: 0.1.0-alpha.23. Last modified: 2026-11-19 14:27 EST. Modified by: mbitar._
<!-- /document-footer -->
