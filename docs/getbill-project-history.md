# getBill project history

_Last modified: 2026-11-17 13:34 EST_

This page records how getBill got to its current state and why the main decisions were made. The
Git history of the repository was reset to a single commit on 2026-11-17. Everything useful that
the 24 earlier commits recorded is kept here, so the reasons behind the code do not depend on the
commit history.

## Releases

Each push to GitHub raises the alpha number by one, so the versions below are pushes, not
planned releases.

| Version | Date | What changed |
| --- | --- | --- |
| Before 0.1.0-alpha.1 | 2026-11-16 | The first tool, called S3 CSV to Excel, converted CSV files in an S3 folder into Excel workbooks. The same morning it gained Parquet input, the secret check before each commit, the flow diagram and the document stamps, and it was renamed getBill. The proprietary license and the demo website followed. |
| 0.1.0-alpha.1 | 2026-11-16 | getBill was marked as an alpha release. The walkthrough page gained steps, speech bubbles and full-screen playback, and the README gained a banner, badges and a feature list. |
| 0.1.0-alpha.2 | 2026-11-16 | The version is set in one place, and every push must raise it. |
| 0.1.0-alpha.3 | 2026-11-16 | Many more test scenarios were added, and GitHub Actions began running every test. |
| 0.1.0-alpha.4 | 2026-11-16 | The Python 3.9 tests moved into the official Python Docker image. |
| 0.1.0-alpha.5 | 2026-11-16 | The README explains how the tests stand in for AWS. |
| 0.1.0-alpha.6 | 2026-11-17 | A checklist of 75 billing-pipeline questions was added, with six findings that could stop getBill from working on real billing data. |
| 0.1.0-alpha.7 | 2026-11-17 | The checklist became a neutral questionnaire for the product owner, and the alpha's limits moved into a separate engineering note. |
| 0.1.0-alpha.8 | 2026-11-17 | The tests run only when code changes, every Monday, and on demand. |
| 0.1.0-alpha.9 | 2026-11-17 | The questionnaire gained 24 scenarios and use cases. |
| 0.1.0-alpha.10 | 2026-11-17 | A Microsoft Lists import file for the questionnaire was added. |
| 0.1.0-alpha.11 | 2026-11-17 | The questionnaire holds questions only, and the answers are kept in a private workbook. |
| 0.1.0-alpha.12 | 2026-11-17 | Every document in `docs/` was renamed to start with `getbill-`. |
| 0.1.0-alpha.13 | 2026-11-17 | The Git history was reset to one commit, and this page was added. |
| 0.1.0-alpha.14 | 2026-11-17 | The questionnaire gained nine questions about government customers and federal compliance, and the engineering note gained the matching gaps. |
| 0.1.0-alpha.15 | 2026-11-17 | The blank requirements workbook is kept in the repository as a template, and a check refuses it once it holds any answer. |
| 0.1.0-alpha.16 | 2026-11-17 | Every document carries the internal-use notice, the last-modified date and time, and "Modified by: mbitar", including LICENSE and every row of the Microsoft Lists file. A test checks every document. |

## Decisions and the reasons for them

### Name and license

- The tool was first called S3 CSV to Excel. It was renamed getBill when it began to read Parquet
  files, because the old name no longer described it.
- getBill is proprietary software owned by FPT. Only FPT employees and contractors may use it, and
  only for FPT's internal business purposes. The package is marked so that it cannot be uploaded to
  the public Python package index (PyPI).

### Accounts and sign-in

- getBill signs in to AWS only with named profiles, including IAM Identity Center (SSO) profiles.
- When the destination bucket is in another AWS account, getBill signs in with a second profile.
  It downloads with the source profile and uploads with the destination profile, so neither bucket
  needs a policy that trusts the other account.
- These two questions, which account owns each bucket and how getBill signs in, were settled before
  any other design question, because every other choice depends on them.

### How values become Excel cells

- A value that looks like a number becomes an Excel number, so sums and sorting work.
- Columns whose heading names an identifier, such as an AWS account ID or an invoice number, always
  stay text. Otherwise Excel shows a 12-digit account ID in scientific notation, such as
  4.44456E+11.
- In Parquet files, an identifier column stored as whole floating-point numbers is written as
  444455556666, not 444455556666.0.
- Leading zeros after a decimal point do not count toward Excel's 15-digit limit, so a cost such as
  0.0000004 becomes a number.
- Parquet columns keep their stored types: numbers stay numbers, timestamps become Excel dates in
  UTC, and map, struct and list columns become JSON text.
- Text that starts with an equals sign is stored as text, so Excel never runs it as a formula.

### Tests and continuous integration

- No test contacts AWS, and GitHub holds no AWS credentials for this repository. The tests use
  moto, a library that simulates the S3 and STS services, together with fake profiles.
- GitHub Actions runs the tests on Python 3.9 and 3.12, and the code coverage must reach 80%.
  GitHub's own machines stopped offering Python 3.9, so each Python version runs inside its
  official Docker image.
- The tests run only when something other than documents, the README banner, the license or the
  version line changes. A scheduled run every Monday at 06:00 UTC catches new library releases, and
  the workflow can also be started by hand.
- getBill stays an alpha release until it has run once against real AWS accounts, because a
  simulation cannot prove how real permissions and encryption behave.

### Versions

- The version is set only in `src/getbill/__init__.py`. `scripts/bump_version.py` raises it and
  updates every place that shows it.
- A pre-push hook refuses a push whose version matches the version already on GitHub, so a
  forgotten version change shows up as a refused push.

### Secrets and private information

- A pre-commit hook refuses commits that add key files, credential files, or lines that look like
  secrets, such as AWS access keys, private keys and tokens. It prints each secret as `[hidden]`.
- A scan on 2026-11-16 found no secret in any commit. The only key-like values were the
  placeholder value "testing" used by the simulated AWS in the tests.

### Requirements

- The questionnaire is written for the product owner and is neutral. It does not say what the alpha
  can or cannot do, so the answers are not limited by today's prototype. What the alpha does today
  is recorded separately, in the [engineering note](getbill-alpha-gap-analysis.md).
- The [questionnaire](getbill-pipeline-questions.md) holds the questions only. The answers are kept
  in a private workbook in SharePoint or OneDrive, which is the source of truth for the
  requirements. Git ignores requirements workbooks, and the pre-commit hook refuses them.
- From version 0.1.0-alpha.15, the repository also keeps one blank copy of the workbook as a
  template, so people can download it. It holds every question and no answers. The pre-commit hook
  checks it with `scripts/check_blank_workbook.py` and refuses it once any answer is typed in, and
  the tests check that it holds the same questions as the questionnaire.
- On 2026-11-17, no compliance or security framework had been chosen. Because most customers are
  expected to be U.S. federal agencies, questions C7 to C15 were added to ask about government
  customers, Controlled Unclassified Information, frameworks such as FedRAMP and NIST SP 800-53,
  AWS GovCloud (US), FIPS 140 encryption, security documents, Section 508 accessibility, and limits
  on who may see the data. The engineering note lists the matching gaps as limitations 16 to 21.

### Documents

- Every document carries a last-modified stamp under its title and a footer that marks it as
  internal and names who modified it. `scripts/stamp_docs.py` writes both.
- Every document in `docs/` starts with `getbill-`, so it is easy to recognize when it is shared.
  `index.html` and `.nojekyll` keep their names, because GitHub Pages needs them.
- The walkthrough page moved from `run-recording.html` to `getbill-run-recording.html` on
  2026-11-17. Links saved to the old address no longer work.

<!-- document-footer -->
---

_Internal use only. Last modified: 2026-11-17 13:34 EST. Modified by: mbitar._
<!-- /document-footer -->
