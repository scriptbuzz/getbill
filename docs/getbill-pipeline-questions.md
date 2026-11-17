# getBill requirements questionnaire

_Last modified: 2026-11-17 13:25 EST_

This questionnaire collects what getBill must do, from where the billing files come from to how
long they are kept. It is written for the product owner and the people who own the data and the
process.

## Where the questions and the answers are kept

- **This page holds the questions only.** It is the master copy of every question, and changes to
  the questions are made here and reviewed like any other change to the repository.
- **The repository also keeps a blank copy of the workbook.** It holds every question, the About
  and Summary worksheets, and the Status choices, with every Answer, Expert and Notes cell empty.
  It is a template to download, not a place for answers.
- **The answers are kept in a private copy of that workbook, not in this repository.** The private
  copy is stored in a SharePoint or OneDrive folder and updated there by the people who answer. It
  is the source of truth for the requirements.
- **Answers never come back into this repository.** Do not paste answers into this page, and do not
  commit a filled-in workbook or a filled-in list export. The secret check that runs before every
  commit refuses the template as soon as any Answer, Expert or Notes cell holds text, or any
  Status says something other than **Not started**. It also refuses every other workbook, even
  when it is added with `git add -f`.

How to answer:

- Write your answer in the **Answer** column of the private workbook. "Not decided yet" and "Does
  not apply" are useful answers too.
- The **Examples of possible answers** column only shows the range of choices. Any answer is
  welcome, including one that is not listed.
- Answer for what the business needs, not for what any existing tool can do today. getBill will be
  built to match these answers.
- Questions in **section 0** shape everything else, so they are the best place to start.
- **Section 10** describes everyday situations, such as month-end close, a customer who leaves
  mid-month, or a late billing file. It works well as a workshop with the people who live through
  these situations.

## Answering together in Excel

The blank workbook [getbill-pipeline-questions.xlsx](getbill-pipeline-questions.xlsx) is generated
from this page and kept in the repository. To start answering, download it, upload it to a private
SharePoint or OneDrive folder, and share it only with the people who answer. From then on, the copy
in that folder is the only copy that holds answers.

The workbook holds every question on this page. Each section has its own worksheet. An About
worksheet explains how to fill it in, and a Summary worksheet counts the questions in each section
by status.

Each question has an **Answer** column, an **Expert** column for the name of the person who gave
the answer, a **Status** column with the choices **Not started**, **Answered**, **Needs
discussion** and **Agreed**, and a **Notes** column.

Store the workbook in SharePoint or OneDrive, and let people edit it there at the same time. Excel
then records who changed each cell and when, under **Review** › **Show Changes**. Excel keeps that
history for about 60 days. No Excel formula can show the last editor of a row, so the Expert column
is typed by hand.

When a question is added or changed on this page, do two things:

1. Regenerate the blank template in the repository, and commit it with the change to this page.
   The tests check that the template holds the same questions as this page, and that it is blank.

   ```bash
   python3 scripts/export_questions_xlsx.py --force
   ```

2. Copy the new or changed question into the private workbook by hand, using the same question ID.
   Do not replace the private workbook with the new template, because the template has no answers.

## Answering together in Microsoft Lists

A private Microsoft List in SharePoint can be used instead of the workbook. Each question
becomes one row that people can edit at the same time. The list records who added each question,
and its version history shows who changed which answer, when, and what it said before.

The file [getbill-pipeline-questions-for-microsoft-lists.csv](getbill-pipeline-questions-for-microsoft-lists.csv)
holds every question in this document, with empty Answer, Status and Notes columns. To create the
list:

1. Download the CSV file from the repository.
2. In Microsoft Lists, or on a SharePoint site, choose **New** › **List** › **From CSV**, and upload
   the file.
3. On the column screen, keep **Title** as the question. Set **Section** and **Status** to
   **Choice**. Set **Why it matters**, **Examples of possible answers**, **Answer** and **Notes** to
   **Multiple lines of text**. Then choose **Create**.
4. Add a **Person** column named **Expert** for the person who gave the answer, and, if you assign questions, a **Person** column
   named **Owner**. A CSV file cannot carry person columns, so they are added here.
5. Edit the **Status** column's choices to **Not started**, **Answered**, **Needs discussion** and
   **Agreed**.
6. In **List settings** › **Versioning settings**, check that version history is on. New lists
   usually have it on already.
7. Share the list: give **Edit** permission to the people who answer, and **Read** permission to
   everyone else.
8. Optional: add a view grouped by **Section**, and a view filtered to **Owner is [Me]**.

Keep the list private, as with the workbook. The list holds the answers, and this page stays the
master copy of the questions. When a question is added or changed on this page, add it to the list
by hand with the same question ID. Do not bring answers back into this page.

If this page changes before the list is created, regenerate the CSV file. The file holds questions
only, so it is safe to keep in the repository:

```bash
python3 scripts/export_questions.py
```

## 0. Goals and users

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| G1 | What business problem should getBill solve, and how will you know it is solved? | The goal decides every other answer and how success is measured. | Finance gets monthly cost reports without manual work. Each customer receives an accurate statement within three business days. Costs are charged back to departments. |
| G2 | Whose AWS costs are these: FPT's own accounts, FPT's customers' accounts, or both? | Billing your own usage and rebilling customers have different rules, recipients and confidentiality. | FPT's internal accounts only. Customer accounts that FPT resells or manages. Both, kept separate. |
| G3 | Who will use getBill, and how technical are they? | It decides the kind of interface and how much must be automatic. | Cloud engineers. Finance analysts. Account managers. Customers themselves. |
| G4 | How should people use it? | A command line, a web page and a fully automatic service are very different products. | A command line. A web page. A request by email or chat. Fully automatic with no person involved. |
| G5 | What should the result look like for each audience? | The output format decides the processing and the delivery. | Excel workbooks. CSV files. PDF statements. A dashboard such as Amazon QuickSight. Rows in a data warehouse. An API. |
| G6 | Which languages and number formats must the output use? | Recipients may expect their local language and formats. | English. Vietnamese. Both. Decimal comma or decimal point. |
| G7 | Which currency must the results show, and where do exchange rates come from? | AWS bills in US dollars, but recipients may need another currency. | US dollars only. Vietnamese dong at the bank's month-end rate. Both side by side. |
| G8 | Is there a deadline or a first milestone? | It decides what to build first. | A first customer report by a given date. Internal use first, customers later. |

## 1. Source: where the billing files come from

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| S1 | Which team or person owns the billing data, and who is the contact when a file is late or wrong? | Someone must fix a broken or missing file. | The cloud operations team. The finance team. An AWS partner or reseller portal. |
| S2 | What produces the billing files? | Each source has its own columns, names and layout. | AWS Data Exports (CUR 2.0). The older AWS Cost and Usage Report. AWS Data Exports in the FOCUS format. A reseller or partner billing portal. Another internal system. |
| S3 | Which AWS accounts do the files cover, and in which account is the export created? | An export in the management (payer) account covers every account. One in a member account covers only that account. | One management account for the whole organization. Several organizations. Each customer's own account. |
| S4 | Are there several sources that must be combined, such as several AWS organizations or other clouds? | Combining sources needs matching rules. | One AWS organization. Several organizations. AWS plus Azure or Google Cloud. |
| S5 | Which columns, filters and details does the export include? | Columns and details decide file size and what recipients can see. | All columns. Selected columns only. Resource IDs included or not. Split cost allocation data for containers. |
| S6 | What time detail does the export have? | Hourly data is many times larger than daily or monthly data. | Hourly. Daily. Monthly. |
| S7 | In which file formats and compression do the files arrive, now and in the future? | The pipeline must read every format that arrives. | Parquet with Snappy, gzip or Zstandard compression. CSV compressed with gzip. ZIP archives. Plain CSV. Excel. JSON. |
| S8 | Where exactly are the files stored, and how are they organized? | The pipeline must find the right files for each month. | An S3 bucket with one folder for each month, such as `BILLING_PERIOD=2026-10`. Several part files for each month. A manifest file that lists the parts. A shared drive. An email attachment. |
| S9 | Should all parts of a month be treated as one data set? | Recipients usually expect one result for each month. | Yes, always join the parts. No, keep each part separate. |
| S10 | How often do new or updated files arrive? | It decides when processing runs. | Several times a day. Once a day. Once a month after the month closes. |
| S11 | Can a closed month change later, and what should happen then? | AWS can restate a month after credits or refunds. Recipients need final numbers and need to know when numbers change. | Ignore changes after the deadline. Reprocess and send a corrected version. Send only the differences. |
| S12 | How large is a typical file, and how large is the largest you expect? | Size decides speed, cost and which output formats can hold the data. | A few megabytes. Hundreds of megabytes. Several gigabytes each month. |
| S13 | In which AWS Regions are the files stored? | Moving data across Regions costs more and may be restricted. | One Region. Several Regions. Data must stay in a given country. |
| S14 | Who may write the files, and who may read them? | Each writer and reader needs its own permissions. | Only AWS Data Exports writes. Only the getBill service reads. Engineers may also read. |
| S15 | How are the source files encrypted, and who controls the keys? | A customer-managed key needs permission for every reader. | S3-managed keys. An AWS KMS key owned by the security team. |
| S16 | How long are source files kept, and can earlier versions be recovered? | An overwritten file can be lost for good. | Kept forever. Kept for 13 months. S3 versioning turned on. |

## 2. Recipients and delivery

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| D1 | Who receives the results? | The recipients decide the content, the format and who may see what. | The finance team. Budget owners for each department. Each customer. Auditors. |
| D2 | How should each recipient receive the results? | Many recipients cannot use cloud storage directly. | An email attachment. A link that expires. A shared drive such as SharePoint or Google Drive. An S3 bucket in their own AWS account. A web portal. |
| D3 | Should each recipient see only part of the data? | Sending all lines to everyone can expose other customers' or departments' costs. | Only their own AWS accounts. Only their cost center or tag. Everything. |
| D4 | How should results be named and organized? | Clear names stop people from opening the wrong month or customer. | By month. By month and customer. By month, customer and version number. |
| D5 | Who may read and who may change the delivered results? | Billing results are confidential. | Only the recipient. The recipient and finance. Read-only for everyone. |
| D6 | Should recipients be told when results are ready, and how? | Without a notice, people use old results or keep checking. | An email. A chat message in Teams or Slack. No notice. |
| D7 | What should happen when results for the same month already exist? | Recipients need to know which version is current. | Replace them. Keep both with a version number. Keep both and mark the old one as replaced. |
| D8 | May results be delivered into another organization's AWS account, and under what rules? | Cross-organization delivery needs agreements and permissions. | Yes, into each customer's own account. No, only into FPT's accounts. |

## 3. Processing and content

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| P1 | What content should each audience receive? | Raw lines, summaries and statements are different products. | Every line item. Totals by account, service, Region or tag. Pivot tables. Charts. An invoice-style statement. |
| P2 | Which cost measure should recipients see? | Each measure gives a different total. | Unblended cost. Net cost after discounts. Amortized cost for Savings Plans and Reserved Instances. Public list price. |
| P3 | Should prices be changed before recipients see them? | Resellers often add a margin, apply a discount, or remove AWS credits. | No changes. Add a markup percentage. Apply a customer-specific discount. Hide credits. |
| P4 | Which columns should recipients see, with what names and in what order? | Raw technical column names are hard for finance users. | All original columns. A short list with plain names. Different columns for each audience. |
| P5 | How should values be shown? | Wrong types break totals and change account IDs. | Costs as numbers with two decimal places. Account IDs as text. Dates in a set format. |
| P6 | Which time zone should dates and times use? | Daily totals change with the time zone. | UTC. Vietnam time. Each recipient's own time zone. |
| P7 | How should tax, credits, refunds and support fees be treated? | They change the totals recipients see. | Show them as separate lines. Include them in the totals. Leave them out. |
| P8 | Where and how should processing run? | It decides reliability, cost and who must be available. | On a person's computer when needed. A scheduled job in AWS. Automatically each time a new file arrives. |
| P9 | What should happen when a month is too large for the chosen output format? | Excel, email and some tools have size limits. | Split it into several sheets or files. Summarize it. Use a different format for large months. |
| P10 | What should happen when one file or one recipient fails? | One failure should not block everyone else. | Continue with the others and report the failure. Stop everything until it is fixed. |
| P11 | Must processing be safe to run again for the same month? | Re-runs happen after failures and restatements. | Yes, a re-run must give the same results without duplicates. |
| P12 | May billing data be copied to a person's computer during processing? | Copies on laptops can leak. | Yes. Only to company-managed computers. No, it must stay in AWS. |

## 4. Sending results back

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| R1 | After processing, who must receive what, besides the recipients in section 2? | The data owner or finance may need a copy or a confirmation. | A copy to finance. A confirmation to the data owner. Nothing more. |
| R2 | Does anyone need a receipt for each run? | A receipt shows that nothing was lost. | A list of files, row counts and totals. A signed summary. No receipt. |
| R3 | Who must be told about failures, and how quickly? | A failure nobody sees means missing reports. | The operations team within an hour. The product owner by the next morning. |
| R4 | Do recipients send anything back, such as approvals, disputes or corrections? | Some processes need a sign-off for each month. | Approval by email. Disputes through a ticket system. Nothing. |

## 5. Archiving and retention

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| A1 | How long must source files and results be kept, and why? | Audit, tax and contract rules can set minimum periods. | Ten years for tax records. Seven years under a contract. Thirteen months. |
| A2 | Where should archives be kept? | Old files cost less in cheaper storage. | S3 Glacier after 90 days. A separate archive account. A records system. |
| A3 | Must archives be impossible to change or delete? | Auditors may need proof that records were not altered. | Yes, with S3 Object Lock. No. |
| A4 | When must files be deleted, and who approves it? | Keeping data too long can also break policy or contracts. | Automatically after the retention period. Only with the data owner's approval. |
| A5 | Should every version of a month's results be kept, or only the latest? | Earlier versions show what recipients saw on each date. | Every version. Only the final version. |

## 6. Security and compliance

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| C1 | How must people and automated jobs sign in to AWS? | Shared keys are hard to control and to revoke. | IAM Identity Center (SSO) for people. IAM roles for automated jobs. No long-term access keys. |
| C2 | How sensitive is this data, and how is it classified? | Account names, tags and resource IDs can reveal customers, projects or people. | Confidential. Internal. Contains personal data. Controlled Unclassified Information (CUI) as marked by a government customer. |
| C3 | Which rules apply, such as contracts, data protection laws or internal policies? | Rules can limit where data goes and who may see it. | Customer contracts. U.S. federal contract clauses. Vietnam's personal data protection rules. The EU General Data Protection Regulation. Company security policy. |
| C4 | Must there be an audit record of who ran what, when, on which files? | Audits and incident reviews need it. | Yes, kept for one year. Yes, through AWS CloudTrail. No. |
| C5 | How must data be encrypted in transit and at rest? | Billing data is confidential. | AWS defaults. A company-managed key for everything. |
| C6 | Who must approve sharing billing data outside the company? | Sending customer costs to the wrong place is a serious incident. | The data owner. Legal. Security. |
| C7 | Are any customers government organizations, and which kinds? | Government customers bring their own security rules, which decide much of the design. | No government customers. U.S. federal civilian agencies. The U.S. Department of Defense. U.S. state or local governments. Governments outside the United States. |
| C8 | How will government customers receive getBill or its results? | A tool FPT runs for a customer, a hosted service, and software installed in the customer's own accounts each fall under different government rules. | FPT runs getBill on FPT's systems and sends the results. FPT hosts getBill as an online service. The customer installs and runs getBill in its own AWS accounts. Not decided yet. |
| C9 | Is any of the billing data Controlled Unclassified Information (CUI), or covered by another government handling rule? | CUI must be protected under NIST SP 800-171, and Defense work may also require CMMC certification. | No. Yes, where the contract marks it as CUI. For some customers only. Not known yet. |
| C10 | Which compliance frameworks, certifications or authorizations must getBill or its operator meet? | The framework sets the security controls, documents and assessments needed before going live. | None. FedRAMP at the Moderate or High level. An agency's authorization to operate (ATO) under NIST SP 800-53. NIST SP 800-171. CMMC Level 2. SOC 2. ISO 27001. |
| C11 | In which AWS environments are the billing files and results stored? | AWS GovCloud (US) has its own Regions, accounts and sign-in, separate from the standard AWS Regions. | Standard AWS Regions. AWS GovCloud (US). Both. AWS Secret or Top Secret Regions. |
| C12 | Must the encryption use cryptographic modules validated under FIPS 140? | Many government contracts require validated encryption for every connection that carries their data. | No. Yes, for every connection to AWS. Yes, for customer data only. |
| C13 | Which security documents must come with getBill for buyers or auditors? | Government buyers often require proof of secure development before they use software. | None. A signed secure software development attestation. A software bill of materials (SBOM). A vulnerability disclosure policy. A system security plan. |
| C14 | Must the results meet accessibility rules? | Section 508 requires files and web pages delivered to U.S. federal agencies to work with assistive technology. | No. Section 508 for every workbook and page. Only for results sent to customers. |
| C15 | Are there limits on who may run getBill or see the data, or on where they work? | Some government contracts and AWS GovCloud (US) workloads allow only certain people, or only work from certain countries. | No limits. U.S. persons only. Work from the United States only. Named people with a background check. |

## 7. Data quality and reconciliation

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| Q1 | How should the results be checked against the source? | A mismatch means lost or changed data. | Totals must match exactly. Totals must match to the cent. Row counts must match. |
| Q2 | Must the results match the AWS invoice for each month? | Finance reconciles against the invoice. | Yes, exactly. Yes, within a stated tolerance. No. |
| Q3 | When is a month final? | Reporting before AWS closes a month gives numbers that change later. | When AWS issues the invoice. A fixed number of days after the month ends. |
| Q4 | What should happen when the source file's columns or layout change? | A changed export can silently break reports. | Stop and alert. Continue and warn. Adapt automatically. |
| Q5 | Who signs off that the results are correct before they are sent? | Errors in customer statements are costly. | Finance reviews each month. Automatic checks are enough. |

## 8. Operations

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| O1 | Who owns and supports getBill, and who is the backup? | Someone must fix it when it fails, even during holidays. | The cloud team, with a named backup. The finance systems team. |
| O2 | By what date or time must results be ready each month? | A deadline decides the schedule and the alerts. | By the third business day. Within one day of each new file. |
| O3 | What budget is there to run it? | Storage, processing and data transfer cost money every month. | A fixed monthly limit. Charged back to each recipient. |
| O4 | How many accounts, customers, files and recipients must it handle now, and in two years? | Growth can pass limits that are safe today. | Ten accounts and one recipient now. Hundreds of customers later. |
| O5 | How should changes to getBill be approved, tested and released? | Untested changes can corrupt reports. | Automatic tests and a review for every change. A test month before each release. |
| O6 | What must be tested with real data before getBill is trusted? | A test with real data shows real sizes, formats and permissions. | One full month for one account. A parallel run beside the current process. |
| O7 | Is there a current manual process that getBill replaces, and when can it stop? | A safe switch-over needs both to run for a while. | An analyst exports Excel files by hand each month. Nothing exists yet. |

## 9. Limits and volumes

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| L1 | What is the most rows one month can have? | Excel holds at most 1,048,576 rows in one sheet, and other formats have their own limits. | Under one million. Several million. Not known yet. |
| L2 | What is the most columns a file can have? | Some exports add one column for each tag key and grow very wide. Excel holds at most 16,384 columns. | Under 150. Several hundred. Not known yet. |
| L3 | How many decimal places must costs keep, and may they be rounded? | Excel keeps only 15 significant digits, so very precise large numbers lose digits. | Keep all decimal places. Round to two places for reports. Round only in summaries. |
| L4 | What is the range of values, from the largest credit to the largest single cost? | A range check catches broken data. | Credits down to minus 100,000 dollars. Single lines up to one million dollars. |
| L5 | What range of dates must be handled, and how precise must times be? | Some tools only store dates in a set range or to the millisecond. | The last ten years. Times to the second. |
| L6 | What is the longest text in one field, such as a list of tags? | Excel holds at most 32,767 characters in one cell. | Short tag lists. Hundreds of tags on some resources. |
| L7 | What is the largest result a recipient can receive and open? | Email systems often refuse attachments over about 20 to 25 MB, and very large workbooks open slowly. | Under 10 MB by email. Any size through a link. |
| L8 | How many files can one month or one run contain, and how long may a run take? | Scheduled jobs often have time limits. | Up to 100 files. A run must finish within one hour. |
| L9 | How long can names be, such as customer names, file names and folder paths? | Some systems limit name lengths, such as Excel sheet names at 31 characters. | Short codes. Full customer names. |
| L10 | What is the largest number of accounts, tag keys and recipients in one month? | Large numbers change how results are split and delivered. | Fifty accounts and twenty tag keys. Thousands of accounts. |

## 10. Scenarios and use cases

Each row describes a situation that billing pipelines commonly meet. For each one, say whether it
applies to you, and what getBill should do when it happens. "Does not apply" is a useful answer.

### Everyday use

| # | Scenario | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| U1 | **Month-end close.** A month ends and AWS finalizes its costs. What should happen, and by when? | This is usually the main reason a billing pipeline exists. | Monthly reports for every recipient by the third business day. One summary for finance, then statements for customers. |
| U2 | **Costs so far this month.** Someone wants to see the current month's costs before it ends. Should getBill support that, and how often? | Month-to-date reports help people act before the month closes, but the numbers still change. | A daily update marked "not final". A weekly update. Only final months. |
| U3 | **Customer statements.** Each customer receives a statement of their AWS costs. What must a statement contain? | Statements often become invoices, so errors cost money and trust. | Totals by service and account. Every line item. FPT's logo and terms. A statement number. |
| U4 | **Chargeback or showback inside the company.** Costs are assigned to departments, projects or cost centers. How are they assigned? | Assigning costs needs clear rules for tags, accounts and shared costs. | By the `CostCenter` tag. By AWS account. By AWS Cost Categories. Untagged costs go to a shared pool. |
| U5 | **Budget tracking.** Someone compares spending with a budget. Should getBill show budgets, and warn when one is exceeded? | Budget warnings need the budget figures and a rule for when to warn. | Show spending against each department's budget. Warn at 80% and at 100%. Not needed, because AWS Budgets is used. |
| U6 | **A sudden jump in cost.** Costs rise unexpectedly, for example after a mistake. Should getBill point it out? | Catching a spike early can save a great deal of money. | Highlight any service that costs 50% more than last month. Not needed, because AWS Cost Anomaly Detection is used. |
| U7 | **Forecast.** Someone wants to know what the month or the year will cost. Should getBill estimate it? | A forecast needs history and a chosen method. | An end-of-month estimate from the daily average. Not needed. |
| U8 | **One-off request.** Someone asks for a specific extract, such as one account's database costs for last quarter. How should such requests be handled? | One-off requests are common and often urgent. | Anyone can run a filtered report themselves. Requests go to the cloud team. Not supported. |
| U9 | **Audit request.** An auditor asks for the billing records of a past period. What must be produced, and how fast? | Audits need complete, unchanged records and proof of where they came from. | The original files and the results for any month in the last ten years, within five business days. |

### Changes to customers and accounts

| # | Scenario | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| U10 | **A new customer or account starts mid-month.** What should their first report or statement cover? | Partial months need a clear start date. | Costs from the day the account was linked. The whole month. Nothing until the next full month. |
| U11 | **A customer or account leaves mid-month.** What should happen to their final report and to their stored data? | Leaving customers need a final statement, and their data may have to be deleted. | A final statement up to the leaving date. Data deleted after 90 days. Data kept for the retention period. |
| U12 | **An account moves between customers, departments or AWS organizations.** Whose report should its costs appear in? | A move splits one account's costs between two owners. | Split by the date of the move. The new owner gets the whole month. |
| U13 | **Past months are needed.** On the first run, or after a correction, earlier months must be processed. How far back? | Back-filling needs the old files to still exist, and can take a long time. | The last 12 months on the first run. Any month on request. Only months from now on. |
| U14 | **Savings Plans and Reserved Instances.** Upfront or monthly commitment fees appear on one account but benefit many. How should they be shown? | The choice changes every recipient's totals. | Spread each fee over the accounts that used it. Show the fee where it was bought. Leave it out. |
| U15 | **Credits and refunds.** AWS credits, promotional credits and refunds arrive. Who gets the benefit? | Credits can be large, and passing them on is a business decision. | Pass credits to the customer whose usage earned them. Keep credits for FPT. Show them on a separate line. |
| U16 | **Shared costs.** Some costs serve everyone, such as the AWS Support plan, shared networks or tax. How should they be divided? | Every shared cost needs a sharing rule, or totals will not add up. | Divide in proportion to each recipient's spending. Charge them to a central budget. Show them separately. |
| U17 | **Prices or margins change mid-month.** A reseller margin or a customer discount changes partway through a month. Which applies to which days? | Mixed rates in one month need a clear rule. | The new rate from the day it changes. The new rate from the next month. |

### When things go wrong

| # | Scenario | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| U18 | **The billing file is late or missing at the deadline.** What should happen, and who should be told? | Recipients wait on the results, and someone must chase the source. | Alert the data owner and wait. Send last month's figures marked as late. Tell the recipients about the delay. |
| U19 | **A file is incomplete, damaged or duplicated.** What should getBill do? | Processing bad data produces wrong results. | Stop and alert. Skip the bad file and continue. Remove duplicate lines automatically. |
| U20 | **AWS changes a month after it was delivered.** See S11. Should the recipients get a corrected version, and how are they told? | A corrected statement can change money already invoiced. | Send a corrected version with the changes marked. Adjust next month's statement instead. |
| U21 | **Wrong results were already sent.** How are they withdrawn and replaced? | A wrong statement can reach a customer or an auditor. | Recall the link and send a corrected version with an explanation. Send a correction notice only. |
| U22 | **A recipient's contact or access changes.** For example, someone leaves the company. How is the list of recipients kept up to date? | Results sent to a former employee or a wrong address are a data leak. | The account manager updates the list. The list comes from the company's directory. |
| U23 | **AWS changes the export's columns or format.** See Q4. Who decides how getBill adapts? | AWS adds and renames columns from time to time. | The cloud team updates getBill within a week. Reports pause until it is fixed. |
| U24 | **Data is lost or a service is down.** For example, the source bucket is deleted, or an AWS Region is unavailable on the deadline. How quickly must getBill recover? | Recovery needs copies of the data and a plan made in advance. | Recover within one business day from a copy in another Region. Wait for AWS to recover. |

<!-- document-footer -->
---

_Internal use only. Last modified: 2026-11-17 13:25 EST. Modified by: mbitar._
<!-- /document-footer -->
