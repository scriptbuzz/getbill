# getBill requirements questionnaire

_Last modified: 2026-11-19 09:39 EST_

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
- Answer **section 2**, billing accounts and access, early. Getting access to each billing source
  takes the longest, because each account owner must approve it.

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
   **Choice**. Set **Why it matters**, **Examples of possible answers**,
   **Answer** and **Notes** to **Multiple lines of text**. Then choose **Create**. The
   **Classification** column says **Internal use only** on every row. The **Questions last
   modified** and **Questions modified by** columns give the date and author of the version of
   this page that the file was made from. A CSV file has no other place for these notes. Keep
   those three columns as **Single line of text**.
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

## About this version of the questions

On 2026-11-19 the questions were rewritten to cover everything getBill needs as a full FinOps
tool, not only billing. The sections follow the capabilities of the FinOps Framework published by
the FinOps Foundation, with extra sections for billing, security and operations. Each question asks
one thing. The question numbers are new, so a private copy made from an earlier version of this
page must be re-created from the new blank workbook.

## 0. Goals and scope

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| G1 | What business problem must getBill solve first? | It sets the priority for every later decision. | Bill customers accurately each month. Show each team what it spends. Cut cloud waste. |
| G2 | How will you measure whether getBill is successful? | A measurable target shows whether the work paid off. | Every bill issued by the third business day. Fewer billing disputes. Cloud spend reduced by 10%. |
| G3 | Is getBill for FPT's own cloud costs, for customers' costs, or for both? | Rebilling customers and managing internal costs have different rules and different users. | FPT's own costs. Customers' costs. Both. |
| G4 | Which capabilities must the first release include? | It decides the scope of the first release. | Billing and invoicing only. Billing plus dashboards and budgets. Full FinOps, including savings recommendations. |
| G5 | Which capabilities can wait for later releases? | It keeps the first release small enough to deliver. | Forecasting. Savings recommendations. Carbon reporting. |
| G6 | Is there a date by which the first release must be in use? | A date decides what can fit in the first release. | A date tied to a customer contract. The start of the fiscal year. No fixed date. |
| G7 | Who makes the final decision when two requirements conflict? | Someone must settle trade-offs quickly. | The product owner. A steering group. The head of finance. |
| G8 | Will getBill be offered to other companies, or used only by FPT and its customers? | Offering it to other companies adds licensing, support and stricter separation of data. | FPT and its customers only. Offered to other companies later. Not decided. |
| G9 | Which existing tools must getBill replace, and which must it work alongside? | Overlap with other tools wastes money and confuses users. | Replaces the Excel workbooks. Works alongside AWS Cost Explorer. Replaces a commercial FinOps tool. |
| G10 | What budget is there to build getBill? | The budget limits the scope and the size of the team. | A fixed amount for the first year. Funded one release at a time. |
| G11 | What budget is there to run getBill each month? | Cloud storage, queries and dashboards cost money every month. | A fixed monthly limit. A share of the cloud spend it manages. Charged to customers. |

## 1. People and roles

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| W1 | Which groups of people will use getBill? | Each group needs its own views and permissions. | The FinOps team. Finance. Engineering teams. Executives. Account managers. Customers. |
| W2 | Roughly how many people in each group will use getBill? | The number of users decides licensing costs and portal capacity. | Five FinOps staff. Fifty engineers. Two hundred customer users. |
| W3 | Is there a FinOps team today, and who is on it? | A FinOps team usually owns getBill's rules and reviews. | A dedicated team. Part of the cloud team. No team yet. |
| W4 | Who is responsible for cloud costs in each business unit or customer? | Reports and alerts need a named person who can act on them. | Each engineering manager. Each customer's finance contact. A central team. |
| W5 | Which groups may change data or settings, and which may only view? | It defines the roles and permissions in getBill. | Finance approves bills. Engineers only view. Account managers change pricing rules. |
| W6 | How technical are the main users? | It decides how much must work without writing queries. | Mostly finance staff who use Excel. Engineers who write SQL. A mix. |
| W7 | Which languages must the screens and reports support? | Users may need their own language. | English. Vietnamese. Both. |
| W8 | Do customers' own staff need to sign in to getBill? | Customer access needs a customer portal and strict separation of each customer's data. | Yes, for every customer. Only for some customers. No, they only receive files. |
| W9 | Which sign-in system must FPT staff use? | Staff should sign in with the accounts they already have. | Microsoft Entra ID. Okta. AWS IAM Identity Center. |
| W10 | Which sign-in system must customers use? | Customers may want to use their own organization's accounts. | Each customer's own identity provider. Accounts that getBill creates. |
| W11 | Must customers be able to manage their own users, or does a central administrator do it? | Letting customers manage their users saves FPT staff time. | A central administrator only. Each customer manages its own users. |
| W12 | What training or help must users get? | Users who do not understand the numbers stop using the tool. | Written guides. Short videos. Training sessions. Explanations inside the screens. |

## 2. Billing accounts and access

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| B1 | Which clouds hold the costs that getBill must cover now? | Each cloud needs its own connection. | AWS. Microsoft Azure. Google Cloud. Oracle Cloud. |
| B2 | Which clouds will be added in the next two years? | Planning for them now avoids a redesign later. | Google Cloud. Oracle Cloud. None. |
| B3 | For each customer and each cloud, who owns the billing account: FPT or the customer? | The owner sets up the billing export and approves access to it. | FPT owns all of them. Each customer owns its own. It differs by customer and by cloud. |
| B4 | How many AWS organizations, Azure billing accounts and Google Cloud billing accounts are there? | Each one needs its own connection and permissions. | One AWS organization. Ten customer AWS organizations. Three Azure billing accounts. |
| B5 | Which Microsoft agreement does each Azure billing account use? | Each agreement type offers different billing exports and permissions. | Enterprise Agreement. Microsoft Customer Agreement. Cloud Solution Provider. Pay-as-you-go. |
| B6 | Through which AWS partner program does FPT resell AWS? | The program decides which billing data, discounts and tools FPT receives from AWS. | The AWS Solution Provider Program. Through an AWS distributor. Both. |
| B7 | May getBill read billing data directly from a customer's cloud account? | Direct access needs the customer's approval and a trust relationship between the accounts. | Yes, through a read-only role. No, the customer must send files. Each customer chooses. |
| B8 | Who at each customer approves giving getBill access to its billing data? | Access stalls without a named approver. | The customer's cloud administrator. Its security team. Its finance lead. |
| B9 | May getBill store long-lived keys or passwords to reach a billing source? | Stored keys must be rotated and can leak. | No, short-lived access only. Yes, if rotated every 90 days. Only for SaaS vendors. |
| B10 | How quickly must getBill's access be removed when a customer leaves? | Access that is left in place is a security risk. | The same day. Within a week. At the end of the contract. |
| B11 | Does FPT also resell Microsoft Azure or Google Cloud? | Reselling another cloud adds that provider's partner billing data and rules. | Microsoft Cloud Solution Provider. Google Cloud partner reselling. AWS only. |
| B12 | Does FPT use AWS Billing Conductor today? | AWS Billing Conductor already applies a reseller's own prices, so getBill may use it or replace it. | Yes, for every customer. For some customers. No. |
| B13 | May resold customers use AWS's own cost tools, such as AWS Cost Explorer, in their accounts? | Customers who see AWS's prices in those tools can find different numbers from FPT's bill. | Yes, showing FPT's prices. Yes, showing AWS's public prices. No access. |

## 3. Cost data sources

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| S1 | Which billing data must getBill read from each cloud? | Each export has a different level of detail. | AWS Cost and Usage Report 2.0. The AWS export in the FOCUS format. Azure Cost Management exports. Google Cloud's billing export to BigQuery. |
| S2 | Must getBill store all cost data in FOCUS, the common billing format of the FinOps Foundation? | A common format makes costs from different clouds comparable. | Yes, FOCUS for everything. FOCUS plus each cloud's own detail. No preference. |
| S3 | How many months of past cost data must getBill load when it starts? | Trends and forecasts need history. | Three months. Thirteen months. Three years. |
| S4 | How up to date must the cost data be? | Fresher data costs more to process. | Updated daily. Updated several times a day. Monthly is enough. |
| S5 | Do you need costs by the hour, by the day or by the month? | Hourly data is much larger, but it shows usage patterns. | By the hour. By the day. By the month. |
| S6 | Must getBill show the cost of each individual resource, such as each server or storage bucket? | Resource detail makes the data much larger, but it shows exactly what costs money. | Yes, always. Only for savings work. No, totals are enough. |
| S7 | Must getBill include purchases made through cloud marketplaces? | Marketplace purchases appear on the cloud bill but belong to other vendors. | Yes. No. Only for some customers. |
| S8 | Must getBill include costs from SaaS vendors? | SaaS bills arrive in different forms and need their own readers. | Microsoft 365. Datadog. Snowflake. None. |
| S9 | Must getBill include costs from data centers, private clouds or software licenses outside the cloud? | The total cost of technology needs every source. | On-premises servers. VMware. Oracle licenses. No. |
| S10 | Must getBill split the costs of shared Kubernetes clusters by team or application? | Shared clusters hide who uses what. | Amazon EKS. Azure Kubernetes Service. Google Kubernetes Engine. No containers. |
| S11 | Must getBill read the providers' list prices and FPT's negotiated prices? | Prices are needed to show discounts and estimate savings. | Yes, both. List prices only. No. |
| S12 | Who is the contact when a provider's billing data is late or wrong? | Someone must chase the provider or the customer. | The cloud team. The customer's administrator. FPT's account manager. |

## 4. Allocation and tagging

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| T1 | How should costs be grouped in reports? | The grouping becomes the structure of every report. | By customer, then project. By business unit, cost center and application. By environment. |
| T2 | How is each customer's or team's usage identified in each cloud? | getBill must know which costs belong to whom. | Whole accounts, subscriptions or projects. Tags or labels on resources. A mix of both. |
| T3 | Is there a tagging policy today, and which tags does it require? | Assigning costs by tags only works when the tags are applied. | Owner, cost center and environment are required. No policy yet. |
| T4 | What share of costs is tagged correctly today? | Poor tagging means much of the cost cannot be assigned. | More than 90%. About half. Unknown. |
| T5 | What should happen to costs that cannot be assigned to anyone? | Costs that belong to nobody must still appear somewhere. | Show them as unassigned. Spread them in proportion to spend. Charge them to a central budget. |
| T6 | May getBill assign costs with its own rules when tags are missing? | Rules can assign costs without changing the cloud resources. | Yes, by account name. Yes, by a mapping table. No. |
| T7 | How should shared costs, such as support plans, networking and security tools, be divided? | Each shared cost needs a rule for dividing it. | In proportion to spend. Evenly. By fixed percentages. Not divided. |
| T8 | How should commitment discounts, such as Savings Plans and reservations, be assigned? | The choice changes each team's or customer's cost. | To the accounts that used them. To the account that bought them. Kept centrally. |
| T9 | How should credits and refunds be assigned? | Credits can be large, and passing them on is a business decision. | To the account that earned them. Kept by FPT. Shared across all customers. |
| T10 | How should tax be shown? | Tax rules differ by country and by customer. | As a separate line. Included in each line. Not shown. |
| T11 | How often may the allocation rules change? | Frequent changes make month-to-month comparisons harder. | Monthly. Quarterly. Rarely. |
| T12 | When an allocation rule changes, should past months be recalculated? | Recalculating changes reports that people have already used. | Yes, always. No, only future months. Only with approval. |
| T13 | Who approves changes to allocation rules? | A rule change moves money between teams or customers. | Finance. The FinOps team. Each customer. |

## 5. Pricing, invoicing and chargeback

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| I1 | Must getBill produce customer invoices, internal chargeback, or reports for information only? | An invoice is a legal document, and a report for information only is not. | Customer invoices. Internal chargeback. Information only. Several of these. |
| I2 | Is getBill's bill the official invoice, or does an accounting system issue the invoice? | An accounting system needs the data in its own format. | getBill issues the invoice. SAP issues it. QuickBooks issues it. |
| I3 | Which kinds of pricing rules apply to customers? | Pricing rules decide what each customer pays. | A markup percentage. A discount. A fixed monthly fee. Different rates for each service. |
| I4 | Do customers receive the discounts that FPT gets from the providers? | Passing discounts on is a business decision that changes FPT's margin. | Yes, all of them. Part of them. No. |
| I5 | Who may change a customer's pricing rules? | A pricing change affects revenue. | Account managers. Finance. The product owner. |
| I6 | Must every pricing change be approved before it takes effect? | Approval stops mistakes before they reach an invoice. | Yes, by finance. Only above a set amount. No. |
| I7 | When a price changes partway through a month, which rate applies to which days? | Two rates in one month need a clear rule. | The new rate from the day of the change. The new rate from the next month. |
| I8 | How often is each customer billed? | It sets the billing schedule. | Monthly. Quarterly. It differs by customer. |
| I9 | By which day must each bill be issued? | The deadline sets the processing schedule. | The fifth business day. The tenth day of the month. |
| I10 | Must someone approve each bill before it is sent? | Approval catches errors before customers see them. | Yes, finance approves every bill. Only bills above a set amount. No. |
| I11 | In which currency must bills be issued? | Customers may need their local currency. | US dollars. Vietnamese dong. The customer's choice. |
| I12 | Where do exchange rates come from, and which day's rate is used? | The rate changes the amount owed. | The bank's month-end rate. The provider's rate. A fixed rate each quarter. |
| I13 | Do any providers bill in a currency other than US dollars? | Totals in different currencies must be converted before they can be added. | All in US dollars. Azure bills some customers in local currency. |
| I14 | What must each bill show? | The content decides how customers can check the bill. | Totals by service. Totals by account. Every line item. A comparison with last month. |
| I15 | How must amounts on a bill be rounded? | Rounding each line or only the total changes the amount owed. | Round only the total. Round each line to two decimal places. |
| I16 | How are billing disputes raised and handled? | Disputes need an owner and a process. | Through the account manager. Through a support ticket. By email to finance. |
| I17 | How is a correction issued after a bill was sent? | A wrong bill must be replaced in a way that can be traced. | A credit note. A corrected bill. An adjustment on the next month's bill. |
| I18 | Must getBill track whether customers have paid? | Payment tracking belongs to accounting unless getBill must do it. | No, the accounting system tracks it. Yes, show paid and unpaid bills. |
| I19 | Which discounts and credits does FPT receive from AWS as a reseller? | These discounts set FPT's margin on each customer. | A partner discount on all usage. Discounts on certain services. Program credits. |
| I20 | Should customers' bills start from AWS public prices or from FPT's own cost? | Starting from public prices keeps FPT's discount private, and starting from cost shows it. | Public prices minus a customer discount. FPT's cost plus a markup. It differs by customer. |
| I21 | How should AWS Support be charged to resold customers? | A reseller can provide support itself or pass on AWS's support charge. | FPT's own support fee. AWS's support charge passed on. Included in the markup. |
| I22 | Which taxes does FPT charge customers on resold AWS usage? | Resale adds taxes that do not appear on AWS's own bill. | Vietnam value-added tax. U.S. sales tax. It depends on the customer's country. |
| I23 | Do resold customers have a minimum monthly spend or a fixed contract term? | A customer who spends less than the minimum must be charged the difference. | A monthly minimum. A yearly commitment. Neither. |

## 6. Reporting and analytics

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| R1 | Which questions must the reports answer for each group of users? | Reports should answer real questions, not just show data. | What did each customer spend? Which services grew? Where is money wasted? |
| R2 | Which measures of cost must reports show? | Each measure gives a different total. | Billed cost. Amortized cost. Cost after discounts. List price. |
| R3 | Which key performance indicators must getBill track? | Indicators show whether cloud spending is under control. | Cost per customer. Share of costs tagged. Commitment coverage. Forecast accuracy. |
| R4 | Which dashboards does each group need? | Each dashboard needs its own data and access rules. | An executive summary. A customer view. A view for each engineering team. |
| R5 | How far back must users be able to compare costs? | Long comparisons need a long history. | The last month. The last 13 months. Three years. |
| R6 | Must users be able to go from totals down to individual resources? | Going down to resources needs detailed data and fast queries. | Yes, to each resource. Only to each service. No. |
| R7 | Must analysts be able to write their own queries on the data? | Self-service queries reduce requests to the engineering team. | Yes, with SQL. Yes, with a report builder. No. |
| R8 | Must users be able to export report data? | Exports let users work in their own tools. | To Excel. To CSV. To PDF. No exports. |
| R9 | Must some reports be sent automatically on a schedule? | Scheduled reports reach people who never sign in. | Weekly by email. Monthly with the bill. No. |
| R10 | Which reporting tool should users see? | The tool decides licensing costs and how reports are built. | Amazon Quick Sight. Microsoft Power BI. A getBill web portal. No preference. |
| R11 | How quickly must a dashboard open? | Slow dashboards drive users away. | In under five seconds. In under thirty seconds. |
| R12 | Must reports show exactly the same numbers as each provider's own cost tools? | Differences from the provider's tools cause doubt. | Yes, exactly. Small differences are acceptable if they are explained. |

## 7. Delivery and notifications

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| D1 | How should each group receive its bills and reports? | Many recipients cannot use cloud storage directly. | A web portal. An email attachment. A file in the customer's own storage. SFTP. |
| D2 | Which file formats must be delivered? | Each format needs its own builder. | PDF. Excel. CSV. Parquet. |
| D3 | Who must receive a copy of each bill besides the customer? | Finance and account managers may need copies. | FPT finance. The account manager. Nobody. |
| D4 | Should recipients be told when a bill or report is ready? | Without a notice, people use old results. | An email. A Microsoft Teams message. No notice. |
| D5 | May results be delivered into a customer's own cloud account? | Delivery outside FPT needs the customer's permission and a trust relationship. | Yes, into the customer's storage. No, only through the portal or by email. |
| D6 | Who must approve sending billing data outside FPT? | Sending data to the wrong place is a serious incident. | The data owner. Security. Legal. |
| D7 | What is the largest file a recipient can receive? | Email systems often refuse attachments over about 25 MB. | 10 MB. 25 MB. No limit, because a download link is sent. |
| D8 | How are lists of recipients kept up to date when people change jobs? | Bills sent to former staff leak data. | The customer updates them in the portal. The account manager updates them. |

## 8. Anomalies

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| N1 | What counts as unusual spending? | Without a clear definition, alerts are either missed or too frequent. | A daily rise of more than 30%. A new service appearing. Spending over a fixed amount. |
| N2 | Should getBill find unusual spending with fixed limits or with statistical models? | Statistical models learn normal patterns, but their alerts are harder to explain. | Fixed limits. Statistical models. Both. |
| N3 | Who must be told about unusual spending? | An alert must reach someone who can act. | The account owner. The FinOps team. The customer. |
| N4 | How quickly must someone be told after unusual spending starts? | Every hour of a runaway cost adds to the bill. | Within hours. By the next day. Weekly. |
| N5 | Through which channel must these alerts arrive? | People ignore alerts in channels they do not watch. | Email. Microsoft Teams. Slack. A ticket in ServiceNow or Jira. |
| N6 | Must people record the cause of unusual spending and what they did about it? | A record shows patterns and proves that action was taken. | Yes, in getBill. Yes, in the ticket system. No. |
| N7 | How many false alarms are acceptable? | Too many false alarms make people ignore every alert. | A few each month. None. |

## 9. Budgets and forecasts

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| F1 | At which levels must budgets be set? | Each level needs its own owner and alerts. | For each customer. For each business unit. For each project. For each account. |
| F2 | Who sets each budget? | Budgets without owners are ignored. | Finance. Each team lead. Each customer. |
| F3 | Should budgets cover a month, a quarter or a year? | The period decides how alerts are calculated. | Monthly. Quarterly. Yearly, with monthly targets. |
| F4 | When should a budget alert be sent? | Early alerts leave time to act. | At 80% of the budget. At 100%. When the forecast passes the budget. |
| F5 | Who must receive budget alerts? | Alerts must reach someone who can act. | The budget owner. Finance. The customer. |
| F6 | How far ahead must getBill forecast costs? | Longer forecasts are less accurate. | To the end of the month. To the end of the quarter. Twelve months. |
| F7 | How accurate must forecasts be? | An accuracy target shows whether forecasts can be trusted. | Within 5%. Within 10%. No target. |
| F8 | Should forecasts include planned changes, such as new projects or migrations? | Forecasts based only on history miss planned growth. | Yes, entered by each team. No, history only. |
| F9 | Must getBill compare each forecast with the actual spending afterwards? | The comparison improves later forecasts. | Yes, every month. No. |
| F10 | Must budgets be read from, or sent to, a financial planning system? | Budgets entered in two places drift apart. | Read from Anaplan. Read from Excel. No other system. |

## 10. Unit economics and business value

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| E1 | Which business measures should cloud cost be compared with? | Cost per unit shows whether spending grows faster than the business. | Cost per customer. Cost per transaction. Cost per active user. |
| E2 | Where do those business measures come from? | getBill must read them from somewhere. | A product database. A finance system. Entered by hand. |
| E3 | Who uses cost per unit, and for which decisions? | The use decides how detailed the figures must be. | Executives, for pricing. Engineers, for design choices. |
| E4 | Must getBill compare costs with targets or industry benchmarks? | Targets show whether a figure is good or bad. | Internal targets. Industry benchmarks. No. |
| E5 | Must getBill show FPT's margin on each customer's cloud resale? | The margin shows which customers are profitable. | Yes, for FPT staff only. No. |

## 11. Commitments and rates

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| K1 | Which commitment discounts are used today? | getBill must track each kind. | AWS Savings Plans. Reserved Instances. Azure reservations. Google Cloud committed use discounts. |
| K2 | Who decides when to buy commitments? | Buying a commitment is a financial decision that lasts one to three years. | The FinOps team. Finance. Each customer. |
| K3 | Must getBill recommend which commitments to buy? | Recommendations need usage history and price data. | Yes. No, the providers' own recommendations are enough. |
| K4 | Must getBill track how much of each commitment is used? | An unused commitment is money spent for nothing. | Yes, daily. Yes, monthly. No. |
| K5 | Which targets apply to commitment coverage and use? | Targets show whether commitments are well managed. | 80% coverage and 95% use. No targets. |
| K6 | Does FPT have negotiated spending agreements with any provider? | getBill must track progress against these agreements. | An AWS private pricing agreement. A Microsoft Azure Consumption Commitment. None. |
| K7 | Must getBill track spending against these agreements? | Falling short of an agreed amount costs money. | Yes. No. |
| K8 | Who receives the savings from commitments bought for customers? | The savings change each customer's price and FPT's margin. | The customer. FPT. Shared between them. |
| K9 | Must getBill show savings from spot capacity and other discounted capacity? | These savings show the value of engineering choices. | Yes. No. |
| K10 | Should commitment discounts be shared across different customers in the same AWS organization? | AWS shares Savings Plans and Reserved Instances across all accounts in an organization unless sharing is turned off. | Yes, FPT shares them and keeps the savings. No, each customer's discounts stay with that customer. |

## 12. Workload optimization

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| O1 | Must getBill find idle or unused resources? | Idle resources are the easiest savings. | Yes. No. |
| O2 | Must getBill recommend smaller or cheaper resource sizes? | Choosing the right size is a large source of savings. | Yes. No, the providers' own tools are enough. |
| O3 | Which kinds of resources must be checked for savings? | Each kind needs its own checks. | Servers. Databases. Storage. Kubernetes. |
| O4 | Who acts on savings recommendations? | Recommendations without an owner are ignored. | Each engineering team. The FinOps team. The customer. |
| O5 | May getBill change resources automatically, such as stopping idle servers? | Automatic changes save money but can cause outages. | No, recommendations only. Yes, in test environments only. Yes, with approval. |
| O6 | Must getBill track the savings that were actually achieved? | Tracking proves the value of the FinOps work. | Yes, for each team. Yes, for each customer. No. |
| O7 | How should savings recommendations reach the people who act on them? | People act on work that appears in their own tools. | A dashboard. A ticket in Jira or ServiceNow. A weekly email. |
| O8 | Must getBill estimate the cost of a planned workload before it is built? | Estimates help teams choose cheaper designs. | Yes. No. |

## 13. Licenses and SaaS

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| L1 | Which software licenses run on cloud resources? | License costs can be larger than the server cost. | Windows Server. SQL Server. Oracle. Red Hat. |
| L2 | Are any licenses brought from your own agreements instead of bought through the cloud? | Your own licenses must be tracked against your contracts. | Yes, Microsoft licenses. No. |
| L3 | Must getBill track SaaS subscriptions and how many seats are used? | Unused SaaS seats are a common waste. | Yes. No. |
| L4 | Where do SaaS costs come from? | Each source needs its own reader. | Vendor invoices. A SaaS management tool. Corporate card statements. |

## 14. Sustainability

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| Y1 | Must getBill report the carbon emissions of cloud usage? | Emissions reports need the providers' carbon data. | Yes, for customers. Yes, for FPT only. No. |
| Y2 | Which providers' carbon data must be included? | Each provider publishes carbon data in its own way. | AWS. Azure. Google Cloud. |
| Y3 | Who uses the emissions reports, and for what? | The use decides the detail and the timing. | Annual sustainability reports. Customer requests. |

## 15. Policy and governance

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| P1 | Which cloud cost policies exist today? | getBill may need to check them. | Required tags. Approved Regions. Approved server types. Spending limits. |
| P2 | Must getBill report how well each policy is followed? | The report shows where the policies fail. | Yes. No. |
| P3 | Must new spending above a set amount be approved before it starts? | Approval stops surprises but slows teams down. | Yes, above a monthly amount. No. |
| P4 | How often should cost reviews take place, and who attends them? | Regular reviews keep costs in view. | Monthly with each team. Quarterly with executives. |
| P5 | Which FinOps maturity level does FPT aim to reach? | The target sets how much process getBill must support. | Crawl. Walk. Run. |
| P6 | Must any spending limits stop or slow usage automatically? | Hard limits protect budgets but can break services. | Yes, for test accounts. No. |

## 16. Customer onboarding

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| U1 | How are new customers added today? | getBill should make this faster. | By email and spreadsheets. Through a request form. |
| U2 | How long may it take to add a new customer? | It sets how much must be automated. | Less than a day. Less than a week. |
| U3 | Which details must be collected for each new customer? | Missing details delay the first bill. | Billing contacts. Accounts. Pricing rules. Currency. |
| U4 | Must customers be able to add their own billing sources? | Self-service saves FPT staff time. | Yes. No, FPT staff add them. |
| U5 | What should a customer's first bill cover when it starts partway through a month? | A partial month needs a clear rule. | Only the days from the start date. The whole month. |
| U6 | What happens to a customer's data when it leaves? | A leaving customer may need its data returned or deleted. | Returned, then deleted. Kept for the retention period. |
| U7 | What happens when an account moves from one customer or team to another? | A move splits one account's costs between two owners. | Costs follow the account from the day of the move. The whole month goes to the new owner. |
| U8 | How many customers will getBill serve now, and in two years? | The number of customers decides the design and the cost. | Ten. One hundred. One thousand. |
| U9 | When a customer starts buying AWS through FPT, do its existing AWS accounts move into FPT's AWS organization? | Moving accounts changes who receives AWS's bill and needs a clear switch-over date. | Yes, the existing accounts move. New accounts are created. Both. |
| U10 | When a customer stops buying AWS through FPT, how are its accounts handed back? | Removing accounts from FPT's organization ends FPT's billing and must match the final bill. | Accounts leave on the last day of the month. Accounts leave immediately. |

## 17. Security and compliance

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| C1 | How sensitive is billing data, and how is it classified? | The classification decides the security controls. | Confidential. Internal. |
| C2 | Which laws, contracts or policies apply to the data? | They limit where the data goes and who may see it. | Customer contracts. Vietnam's personal data protection decree. GDPR. |
| C3 | Which security framework must getBill meet? | The framework sets the controls and the documents. | NIST SP 800-53 Moderate. ISO 27001. SOC 2. None. |
| C4 | Are any customers government organizations? | Government customers bring their own security rules. | No. U.S. federal agencies. State or local governments. |
| C5 | Is any billing data Controlled Unclassified Information (CUI)? | CUI must be protected under NIST SP 800-171. | No. Yes. Not known. |
| C6 | Will getBill or any customer need a government cloud? | Government clouds have their own accounts, sign-in and rules. | No. AWS GovCloud (US). Azure Government. |
| C7 | Must the encryption use cryptographic modules validated under FIPS 140? | Many government contracts require it. | Yes. No. |
| C8 | Who must control the encryption keys? | Keys that a customer controls need extra permissions for every reader. | The cloud provider. FPT. Each customer. |
| C9 | In which countries or Regions must billing data stay? | Data residency rules limit where data can be stored. | The United States. Vietnam. Anywhere. |
| C10 | May billing data from Azure and Google Cloud be copied into AWS? | Some rules forbid moving data from one provider to another. | Yes. No. |
| C11 | Must each customer's data be stored apart from other customers' data? | Separate storage adds cost and setup work. | Shared storage with strict access rules. A separate account for some customers. A separate account for every customer. |
| C12 | Are there limits on who may see the data, or on where they work? | Some contracts allow only certain people or countries. | Only U.S. persons. Only FPT staff. |
| C13 | May billing data be copied to a person's computer? | Copies on laptops can leak. | Yes. Only to company-managed computers. No. |
| C14 | Which security documents must come with getBill for customers or auditors? | Buyers often ask for proof of secure development. | A system security plan. Penetration test results. A software bill of materials. |
| C15 | Must reports and the portal meet accessibility rules? | Section 508 applies to software used by U.S. federal agencies. | Yes, Section 508. Yes, WCAG 2.1 level AA. No. |

## 18. Data quality and month close

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| Q1 | Must getBill's totals match each provider's invoice? | Finance checks the bills against the invoice. | Yes, to the cent. Within a stated tolerance. No. |
| Q2 | When is a month final? | Reporting before a provider closes a month gives numbers that change later. | When the provider issues the invoice. A set number of days after the month ends. |
| Q3 | What should happen when a provider changes a month after it was billed? | Providers restate months after credits or refunds. | Issue a corrected bill. Adjust the next month's bill. Ignore small changes. |
| Q4 | What should happen when billing data is late or missing on the deadline? | Customers are waiting for the bill. | Wait and alert. Issue an estimated bill. Bill without that source. |
| Q5 | Which checks must pass before a bill is released? | Checks catch errors before customers see them. | Totals match the invoice. No unassigned costs. Large changes reviewed. |
| Q6 | Who must be told when a check fails, and how quickly? | A failure that nobody sees means a late or wrong bill. | The operations team within an hour. The product owner the next day. |
| Q7 | When a month is processed again, should the earlier results be replaced or kept as a version? | Earlier versions show what recipients saw on each date. | Keep every version. Replace them. |

## 19. Retention and archiving

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| A1 | How long must raw billing data be kept? | Tax, audit and contract rules set minimum periods. | 13 months. Seven years. Ten years. |
| A2 | How long must issued bills be kept? | Bills are financial records. | Seven years. Ten years. |
| A3 | How long must audit records of who did what be kept? | Investigations need old records. | One year. Seven years. |
| A4 | Must issued bills be impossible to change or delete? | Auditors need proof that records were not altered. | Yes. No. |
| A5 | How quickly must records be produced for an auditor? | Some audits have short deadlines. | Within a day. Within a week. |
| A6 | Who approves deleting data after its retention period ends? | A deletion must not break a legal hold. | It happens automatically. Finance approves. Legal approves. |

## 20. Integrations

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| X1 | Which accounting system must receive billing data? | Each system needs its own format or connection. | SAP. Oracle NetSuite. QuickBooks. None. |
| X2 | Which ticket system should getBill send work to? | Teams act on tickets in their own tools. | Jira. ServiceNow. None. |
| X3 | Which chat tools should getBill send messages to? | Alerts in chat get faster responses. | Microsoft Teams. Slack. None. |
| X4 | Must getBill read resource owners from a configuration management database? | A configuration management database can tell getBill who owns each resource. | ServiceNow. None. |
| X5 | Must other systems be able to read getBill's data through an API? | An API lets other tools reuse the data. | Yes. No. |
| X6 | Must getBill send its data to a company data warehouse? | A data warehouse lets other teams combine cost data with other data. | Snowflake. Amazon Redshift. None. |

## 21. Operations and service levels

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| V1 | Who owns and supports getBill day to day? | Someone must fix it when it fails. | The cloud team. A dedicated FinOps engineering team. |
| V2 | During which hours must support be available? | Support hours decide the staffing. | Business hours in Vietnam. Around the clock. |
| V3 | How much downtime is acceptable for the portal and dashboards? | The availability target decides the design and its cost. | 99.9% available. 99% available. Best effort. |
| V4 | How quickly must getBill recover after a failure on a billing day? | The recovery time decides backups and failover. | Within four hours. Within one day. |
| V5 | How much data may be lost after a failure? | It decides how often data is backed up. | None. One day. One week. |
| V6 | How large is a month's billing data today, and how fast is it growing? | Size decides storage and processing costs. | A few gigabytes. Hundreds of gigabytes. Doubling each year. |
| V7 | How must changes to getBill be tested and approved before release? | Untested changes can corrupt bills. | Automatic tests and a review. A test environment first. |
| V8 | Which separate environments are needed? | Separate environments keep test changes away from real bills. | Development, test and production. Production only. |

## 22. Moving from today's process

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| M1 | Which manual steps are used today to produce bills and reports? | Each step must be rebuilt in getBill. | Exporting data. Copying it into Excel. Running macros. Emailing files. |
| M2 | Which Excel workbooks and VBA macros are used today? | Each one must be listed before it can be replaced. | One workbook for each customer. A shared pricing workbook. |
| M3 | Who maintains each workbook and macro? | The people who maintain them know the hidden rules. | A finance analyst. The cloud team. |
| M4 | How long should getBill and the old process run side by side? | Running both shows whether getBill's results match. | One month. Two months. Until finance approves. |
| M5 | What must match before the old process stops? | A clear test prevents surprises for customers. | Every customer's total, to the cent. Totals within 1%. |
| M6 | Which customers still need Excel files, and until when? | It decides how long Excel output must be kept. | None. Some, until their contracts renew. |
| M7 | Which past bills must be loaded into getBill? | Customers may ask about old bills. | None. The last 12 months. |

<!-- document-footer -->
---

_Internal use only. Last modified: 2026-11-19 09:39 EST. Modified by: mbitar._
<!-- /document-footer -->
