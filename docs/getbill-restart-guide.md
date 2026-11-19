# getBill restart guide

_Last modified: 2026-11-19 16:38 EST_

_Version: 0.1.0-alpha.25_

This guide is for anyone who picks up getBill after a break. It says where the project stands, how
to set up a computer to work on it, which routine steps each kind of change needs, and which
questions are still open. The [project history](getbill-project-history.md) explains how the
project got here and why the main decisions were made.

## Where the project stands

These facts were true on 2026-11-19, at version 0.1.0-alpha.25.

- getBill works as an interactive command-line tool. It converts CSV and Parquet files, including
  AWS CUR 2.0 billing exports, from an S3 folder into Excel workbooks, and uploads the workbooks to
  a folder in the same bucket, in another bucket, or in a bucket in another AWS account.
- getBill is still an alpha release. It has only been tested against a simulated AWS, never
  against real AWS accounts or real billing exports.
- The tests run on GitHub Actions on Python 3.9 and 3.12, and the code coverage must reach 80%.
  The test runs for versions 0.1.0-alpha.15 and 0.1.0-alpha.16 failed, because Git inside the test
  container refused to read a folder that belongs to another user. Version 0.1.0-alpha.17 fixed
  the test, and its run passed on both Python versions.
- The product owner has not answered the requirements questionnaire yet.
- On 2026-11-19 the project owner recorded the first product decisions in the
  [product document](getbill-product.md). getBill is a billing product first, release 1 covers AWS
  and Azure, and the security target is the NIST SP 800-53 Revision 5 Moderate baseline. Read the
  product document before any design work.
- FPT resells AWS to its customers, so the questions and the design cover reseller billing: FPT's
  payer accounts, AWS Billing Conductor, and the price that FPT charges each customer.
- The requirements questionnaire has 216 questions in 23 sections that cover the full FinOps scope.
- The [slide presentation](getbill-product-overview.pdf) presents getBill as a FinOps solution in
  26 slides. Its charts use sample figures.
- The [AWS architecture diagram](getbill-aws-architecture.svg) shows the planned design for
  collecting billing data from AWS, Azure and Google Cloud. Nothing in it is built yet. It agrees
  with the product document.
- Every document shows the getBill version next to its date and time, under the title and in the
  footer. The version script and the pre-push hook keep the version current.
- The repository lives at `github.com/scriptbuzz/getbill`, and all work happens on the `main`
  branch. GitHub Pages publishes the `docs/` folder at `https://scriptbuzz.github.io/getbill/`.

## Set up a computer

getBill needs Python 3.9 or newer and Git. Run these commands once on each new computer.

1. Copy the repository and open its folder:

   ```bash
   git clone https://github.com/scriptbuzz/getbill.git
   ```

   ```bash
   cd getbill
   ```

2. Turn on the repository's Git hooks. Git does not turn them on by itself. Without them, nothing
   stops a commit that holds a secret, or a push that forgets to raise the version.

   ```bash
   git config core.hooksPath .githooks
   ```

3. Check that commits will carry the right author. The command must print the project owner's
   email address. If it prints nothing or another address, set it with `git config user.email`.

   ```bash
   git config user.email
   ```

4. Create a Python virtual environment and install getBill together with its test libraries:

   ```bash
   python3 -m venv .venv
   ```

   ```bash
   .venv/bin/pip install -e '.[test]'
   ```

5. Run the tests. They use a simulated AWS, so they need no AWS account and no AWS credentials.

   ```bash
   .venv/bin/pytest -q
   ```

## Routine steps for each kind of change

### A change to the code

1. Change the code and its tests, then run `.venv/bin/pytest -q`.
2. Commit the change. The pre-commit hook checks the staged files for secrets first.

### A change to a document

Every document carries a "Last modified" stamp under its title, followed by the getBill version,
and a footer that says "Internal use only", gives the same version, date and time, and names who
modified it. After you change a document, run the stamp script, which updates both stamps in every
changed document:

```bash
python3 scripts/stamp_docs.py --changed
```

A new Markdown file in `docs/` gets its stamps the first time the script runs. A new SVG diagram or
HTML page needs two elements first, one with `id="last-modified"` and one with
`id="document-footer"`, which the script then fills in. Every file name in `docs/` starts with
`getbill-`, except `index.html` and `.nojekyll`, which GitHub Pages needs.

### A change to the AWS architecture diagram

The diagram is built by a script from the official icon packages of AWS, Microsoft Azure and
Google Cloud. The icon packages are not kept in the repository. The script's notes say where to
download them and how to unzip them. Change the layout or the text in the script, not in the SVG
file, then rebuild the diagram:

```bash
python3 -I scripts/build_architecture_diagram.py <icons folder> docs/getbill-aws-architecture.svg
```

Open the diagram in a browser afterward and check that no text is clipped or overlapping.

### A change to the requirements questions

The questionnaire [getbill-pipeline-questions.md](getbill-pipeline-questions.md) holds the
questions only. The answers never enter the repository. They live in a private workbook in
SharePoint or OneDrive, which is the source of truth for the requirements.

1. Change the question on the questionnaire page. Keep each question neutral: describe the need,
   not what the alpha can or cannot do. What the alpha can do belongs in the
   [engineering note](getbill-alpha-gap-analysis.md).
2. Run the stamp script. Because the questionnaire changed, it also regenerates the Microsoft Lists
   file, `getbill-pipeline-questions-for-microsoft-lists.csv`.
3. Regenerate the blank workbook template. The `--force` option allows the script to replace the
   template that is already in the repository.

   ```bash
   python3 scripts/export_questions_xlsx.py --force
   ```

4. Check that the template holds no answers. The pre-commit hook runs the same check and refuses a
   template that holds any answer.

   ```bash
   python3 scripts/check_blank_workbook.py docs/getbill-pipeline-questions.xlsx
   ```

5. Copy the new or changed question into the private workbook by hand, with the same question ID.
   Never replace the private workbook with the template, because the template has no answers.

### Before every push

Raise the version. The script changes the version in `src/getbill/__init__.py` and in every page
that shows it. The pre-push hook refuses a push whose version is not newer than the version on
GitHub.

```bash
python3 scripts/bump_version.py
```

The script then stamps every document that differs from GitHub with the new version, so each
document in the push shows the version that the push carries. The pre-push hook refuses a push
that changes a document without the new version. Then add a row for the new version to the
release table in the [project history](getbill-project-history.md), and run the stamp script again.

## Open questions and unfinished work

1. **The compliance target may still rise.** The project owner chose the NIST SP 800-53
   Revision 5 Moderate baseline as the design target on 2026-11-19, without seeking a formal
   authorization yet. Questions C3 to C7, C12, C14 and C15 in the questionnaire ask the product owner about
   government customers, Controlled Unclassified Information, AWS GovCloud (US), FIPS 140
   encryption, security documents, Section 508 accessibility, and limits on who may see the data.
   Their answers may require a stricter target.
2. **The questionnaire has no answers yet.** The questions were rewritten on 2026-11-19 to cover
   the full FinOps scope, and their numbers changed. A private workbook made from an earlier version
   must be re-created from the new blank workbook.
3. **getBill has never run against real AWS.** The engineering note lists 21 known limitations.
   The first ones to check on real billing exports are gzip-compressed CSV files (limitation 1),
   month subfolders and the export's manifest file (limitation 2), and the Excel row limit
   (limitation 3). getBill stays an alpha release until a run against real accounts succeeds.
4. **The old walkthrough address no longer works.** The page moved from `run-recording.html` to
   `getbill-run-recording.html`. A small page at the old address that sends visitors to the new one
   would repair saved links.
5. **The slide presentation does not show the version yet.** The PDF is built outside the
   repository, so the stamp script cannot reach it. Add the version and the date to the title
   slide the next time the slides are rebuilt, and keep the slide files in the repository.
6. **Two sign-in choices in the architecture are still proposals.** For Azure, the design proposes
   an Entra ID application that trusts a signed token from AWS, so that no secret is stored. For
   Google Cloud, it proposes Workload Identity Federation for the AWS Glue job that reads BigQuery.
   Both must be tested before they are relied on.
7. **The test packages are not installed on the current Mac.** The project's `.venv` folder lacks
   pytest and openpyxl, so run step 4 of "Set up a computer" before running the tests there. Until
   then, `/usr/bin/python3` has openpyxl and can rebuild the blank workbook, and GitHub Actions runs
   the full tests on every push.
8. **GitHub may still show the old commits.** The Git history was reset to one commit on
   2026-11-17. GitHub can keep serving an old commit to anyone who has its direct link until GitHub
   removes unreferenced commits. A scan on 2026-11-16 found no secret in any old commit, so this is
   a matter of tidiness, not of security.

## Where each document is

| Document | What it holds |
| --- | --- |
| [README.md](../README.md) | How to install, run and test getBill, which AWS permissions it needs, and how the version, secret check and stamps work. |
| [getbill-product.md](getbill-product.md) | What getBill is for, who uses it, what each release must do, the decisions made so far, and how getBill is built. |
| [getbill-product-overview.pdf](getbill-product-overview.pdf) | The slide presentation of getBill as a FinOps solution, with a technical appendix. Its charts use sample figures, not real customer data. |
| [getbill-project-history.md](getbill-project-history.md) | Every version, and the reasons behind the main design decisions. |
| [getbill-pipeline-questions.md](getbill-pipeline-questions.md) | The requirements questionnaire for the product owner, with questions only. |
| [getbill-pipeline-questions.xlsx](getbill-pipeline-questions.xlsx) | The blank workbook template, which people download to start answering. |
| [getbill-pipeline-questions-for-microsoft-lists.csv](getbill-pipeline-questions-for-microsoft-lists.csv) | The same questions as a file that Microsoft Lists can import. |
| [getbill-alpha-gap-analysis.md](getbill-alpha-gap-analysis.md) | What the alpha does today and its 21 known limitations, each linked to the questions it depends on. |
| [getbill-flow-diagram.svg](getbill-flow-diagram.svg) | A diagram of how getBill moves files from S3, through the computer, and back to S3. |
| [getbill-aws-architecture.svg](getbill-aws-architecture.svg) | The planned AWS architecture that collects billing data from AWS, Azure and Google Cloud, converts it to FOCUS 1.2 and shows it in dashboards. `scripts/build_architecture_diagram.py` builds it. |
| [getbill-run-recording.html](getbill-run-recording.html) | A step-by-step walkthrough of one getBill run, published on GitHub Pages. |
| [LICENSE](../LICENSE) | The proprietary license. Only FPT employees and contractors may use getBill. |

<!-- document-footer -->
---

_Internal use only. Version: 0.1.0-alpha.25. Last modified: 2026-11-19 16:38 EST. Modified by: mbitar._
<!-- /document-footer -->
