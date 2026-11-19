# getBill product document

_Last modified: 2026-11-19 08:28 EST_

This document describes what getBill is, who it serves, what each release must do, and how it is
built. It is the reference for product and design decisions from now on. When a decision changes,
change this document first.

**Status: draft.** The project owner made the decisions in the
[recorded decisions](#recorded-decisions) section on 2026-11-19. The product owner has not yet
answered the [requirements questionnaire](getbill-pipeline-questions.md). Where those answers
differ from this document, update this document. Statements marked **Proposed** are design
suggestions that nobody has approved yet.

## Purpose

getBill turns cloud billing data into accurate bills and cost statements for each customer.
Billing comes first. Features that help customers understand and reduce their spending, which the
FinOps Foundation calls FinOps capabilities, come in later releases.

Today, parts of this work are done in Excel workbooks with VBA macros. getBill replaces that
Excel and VBA processing. getBill still produces Excel workbooks during the transition, because
people and processes rely on them today, but Excel is a transitional output and will be phased
out.

## Who uses getBill

| User | What they need from getBill |
| --- | --- |
| FPT operations staff | They onboard customers and billing sources, run and monitor the pipelines, and correct problems. |
| FPT billing staff | They check each customer's bill against the cloud provider's invoice, approve it, and issue corrections. |
| FPT administrators | They manage who can sign in, what each person may see, and how getBill is configured. |
| Customer finance staff | They sign in to see their own bills, costs, budgets and alerts, and receive their reports. |
| Customer engineers | They sign in to see which accounts, services and tags drive their costs. |
| Auditors | They need a record of every bill issued, every correction, and every change of access. |

Every customer user sees only their own customer's data.

## Scope by release

### Release 1

- **Cloud providers:** AWS and Microsoft Azure.
- **Capabilities:** getBill brings in the billing data, assigns every cost line to a customer and
  within a customer to accounts, teams or tags, prices it with each customer's rules, produces a
  bill or cost statement checked against the provider's invoice, shows reports and dashboards,
  warns about unusual spending, and tracks spending against budgets.
- **Delivery:** Customers download reports from a customer portal, receive them by email, or
  receive them in an S3 bucket they own.
- **Report formats:** Excel workbooks written by getBill's own converter, and dashboards.
- **Where getBill runs:** A commercial AWS Region.

### Later releases

- Google Cloud billing data, and then billing data from SaaS vendors.
- Forecasting, cost per unit of business (unit economics), savings recommendations for commitment
  discounts and resource sizes, and software license costs.
- Delivery by SFTP.
- A version of getBill that runs in AWS GovCloud (US), for customers that require it.
- Retiring Excel output once customers' processes no longer depend on it.

## Recorded decisions

| Topic | Decision | What it means for the design |
| --- | --- | --- |
| Purpose | getBill is a billing product first, and FinOps features follow later. | Accurate allocation, pricing and reconciliation come before analysis and optimization. |
| Who owns the AWS payer accounts | Some customers' accounts sit inside FPT's AWS Organizations, and other customers keep their own payer accounts. | getBill must accept billing data both from FPT's own payer accounts and from payer accounts that customers own. |
| How getBill reads customer-owned billing data | Each customer chooses one of two methods during onboarding. | getBill supports direct delivery of the customer's billing export into getBill's S3 bucket, and reading the customer's own bucket through an IAM role the customer creates. |
| Who signs in | FPT staff and customers both sign in. | getBill needs a customer portal, per-customer access rules, and sign-in through each organization's own identity provider. |
| Where getBill runs | getBill runs in a commercial AWS Region first, and a GovCloud version follows when a customer requires it. | The design must avoid choices that only work in commercial Regions, or record them as known work for the GovCloud version. |
| Release 1 capabilities | Release 1 covers allocation, invoicing and chargeback, reports and dashboards, and alerts and budgets. | Forecasting and optimization wait for later releases. |
| Pricing | Each customer has its own pricing rule: a markup, a discount, or the provider's cost unchanged. | Pricing rules are stored per customer and applied before any bill is produced. |
| Customer data separation | Customers share storage by default, and a customer that requires it gets its own AWS account. | Shared storage must be divided by customer and protected by access rules, and the design must also run in a dedicated account per customer. |
| Excel reports | getBill's own converter writes the Excel workbooks. | The existing converter, with its rules for account IDs and number precision, moves into the reporting component. Excel is transitional. |
| Security and compliance target | getBill is designed to the NIST SP 800-53 Revision 5 Moderate controls, without seeking a formal authorization yet. | Encryption, audit records, access control and secure development practices follow the Moderate baseline, which FedRAMP Moderate is also based on. |
| Delivery in release 1 | Reports reach customers through the customer portal, by email, and in the customer's own S3 bucket. | SFTP waits for a later release. |
| Cloud providers in release 1 | Release 1 supports AWS and Azure, and Google Cloud follows. | Billing data from every provider is stored in one common format from the start. |

## How to think about getBill

getBill is described at three levels. Each level answers one question, and each level exists to
serve the one above it.

1. **Purpose: why getBill exists.** The [purpose](#purpose) section answers this.
2. **Capabilities: what getBill must be able to do.** The capabilities use the names from the
   [FinOps Framework](https://www.finops.org/framework/), so that people inside and outside FPT
   share the same words.
3. **Components: how getBill is built.** Each component provides one or more capabilities, and
   nothing is built for a capability that is not in scope.

### Capabilities

| Capability | What it means for getBill | Release |
| --- | --- | --- |
| Data ingestion | getBill brings in billing data from every source and keeps the original files unchanged. | 1 |
| Allocation | getBill assigns every cost line to a customer, and within a customer to accounts, teams or tags. | 1 |
| Invoicing and chargeback | getBill prices each customer's costs with that customer's rules and produces a bill or cost statement that matches the provider's invoice. | 1 |
| Reporting and analytics | getBill produces reports and dashboards for FPT staff and for each customer. | 1 |
| Anomaly management | getBill warns when a customer's spending changes unusually. | 1 |
| Budgeting | getBill tracks each customer's spending against a budget and warns before the budget runs out. | 1 |
| Policy and governance | getBill controls who sees what, records every change, and keeps issued bills unchanged. | 1 |
| Forecasting | getBill predicts each customer's spending for the coming months. | Later |
| Unit economics | getBill reports cost per unit of a customer's business, such as cost per user. | Later |
| Rate optimization | getBill recommends commitment discounts, such as Savings Plans and reservations. | Later |
| Workload optimization | getBill recommends resource sizes and removal of unused resources. | Later |
| Licensing and SaaS | getBill includes software license and SaaS costs. | Later |

### Components

The components never call each other directly. Each one reads its input from an agreed storage
area and writes its output to the next one, so any component can be rebuilt or replaced on its
own.

**Setup**

1. **Customer registry.** It records each customer, the AWS accounts and Azure subscriptions that
   belong to it, its pricing rule, its budget, the people who receive its reports, and its contract
   dates. Every other component reads from it.
2. **Billing source onboarding.** It registers a new billing source, proves access with a test
   pull, and sets up the provider's side from a template.
3. **User onboarding and access.** It signs people in through their own organization's identity
   provider, gives each person a role, and ties every customer user to exactly one customer.
4. **Customer offboarding.** It issues the final bills, withdraws access, and returns or deletes
   the customer's data as the contract requires.

**Security**

5. **Access to billing sources and delivery targets.** It gives each pipeline short-lived access
   to each source and destination, and avoids stored passwords and keys wherever the provider
   allows it.
6. **Encryption keys.** It encrypts each storage area with its own key in AWS Key Management
   Service (KMS), and a customer with its own AWS account can have its own key.
7. **Audit trail.** It records who read or changed data, which bill went to whom and when, and
   every change of access.

**Data processing**

8. **Billing data pull pipeline.** It runs one connector per provider and stores every file
   unchanged, with a record of its source, the time of the pull and a checksum. Running a pull
   twice gives the same result.
9. **Catalog and schema tracking.** It registers every table in the AWS Glue Data Catalog,
   divides the data by provider, billing account and billing month, and warns when a provider
   changes its columns.
10. **Transformation and preparation.** It converts every source to the common format, maps each
    cost line to a customer, applies the customer's pricing rule, spreads commitment discounts and
    shared costs, and converts currencies.
11. **Data quality and reconciliation.** It checks row counts, duplicates and totals against the
    provider's invoice. Only data that passes these checks is used for bills.
12. **Billing month status.** It tracks each month for each source as open, estimated, final or
    restated, and reprocesses a month when the provider rewrites it.

**Results for people**

13. **Bills and reports.** It produces each customer's bill or cost statement and its reports, and
    gives every issued bill a version number, so a corrected bill never silently replaces the old
    one. getBill's own converter writes the Excel workbooks.
14. **Dashboards.** It shows dashboards in Amazon Quick Sight, where each customer user sees only
    their own customer's rows.
15. **Spending alerts and budgets.** It compares each customer's spending with its usual pattern
    and with its budget, and warns the customer and FPT staff.
16. **Delivery.** It delivers bills and reports through the customer portal, by email, and to the
    customer's own S3 bucket. It retries failed deliveries and keeps a receipt for each one.
17. **Archiving and retention.** It moves old data to cheaper storage, deletes data when its
    retention period ends, and locks issued bills so that nobody can change or delete them.
18. **Corrections.** It lets FPT billing staff reissue a bill, add a credit or a one-off charge,
    and record the reason.

**Operations**

19. **Orchestration, scheduling and monitoring.** It starts each step when new data is stored or
    on a schedule, tracks every run, and alerts FPT operations staff when a source stops delivering
    or a bill misses its due date.
20. **Deployment, environments and recovery.** It defines every AWS resource as code, uses
    separate development, test and production accounts, copies data to a second AWS Region, limits
    getBill's own AWS costs, and can pull any month again from the provider.

## How billing data moves

Billing data passes through four storage areas in Amazon S3, each registered in the AWS Glue
Data Catalog and queried with Amazon Athena:

1. **Raw.** Billing files exactly as each provider delivered them.
2. **Normalized.** Every provider's data in one common format.
3. **Curated.** Data that is mapped to customers, priced, checked and approved for billing.
4. **Output.** Issued bills and reports, with every version kept.

When a component finishes, it publishes an Amazon EventBridge event, and AWS Step Functions starts
the next step.

### The common format

getBill stores every provider's data in the FinOps Open Cost and Usage Specification (FOCUS),
version 1.2, as Parquet files. FOCUS is an open standard from the FinOps Foundation, and AWS, Azure
and Google Cloud all export it. FOCUS gives every provider the same column names, such as the
billing account, the sub-account, the billed cost, the effective cost after discounts, and the
invoice ID.

For AWS, getBill also keeps the detailed Cost and Usage Report 2.0 (CUR 2.0), because FOCUS leaves
out some AWS details that bills and analysis may need.

**Known risk:** Microsoft offers its FOCUS 1.2 export as a preview, and some of its columns are not
filled in yet. Until it is generally available, getBill must either accept those gaps or read
Azure's FOCUS 1.0 export, which is generally available.

### Access to billing sources

| Source | How getBill receives the data |
| --- | --- |
| AWS payer accounts owned by FPT | AWS Data Exports delivers CUR 2.0 and FOCUS files from each payer account straight into getBill's S3 bucket, so getBill holds no credentials for those accounts. |
| AWS payer accounts owned by customers | The customer chooses either direct delivery of its export into getBill's S3 bucket, or an IAM role that getBill assumes to read the customer's own bucket. The role requires an external ID, a value shared only between FPT and that customer, which stops another party from tricking getBill into using the role. |
| Azure billing accounts | Azure Cost Management exports FOCUS data into an Azure storage account. **Proposed:** getBill reads it with an Entra ID application that trusts a signed token from AWS, so no secret is stored. If that is not possible, getBill keeps a certificate or a storage access token in AWS Secrets Manager and rotates it. AWS DataSync or a scheduled job copies the files into S3. |
| Google Cloud, in a later release | Google Cloud exports FOCUS data to BigQuery. getBill signs in through Google's Workload Identity Federation, which trusts getBill's AWS role directly, so no key file is stored. |

### Pricing

Each customer's pricing rule is stored in the customer registry and applied during
transformation. **Proposed:** getBill applies pricing rules itself instead of relying on AWS
Billing Conductor, for two reasons. Billing Conductor only works on accounts inside FPT's own AWS
Organizations, and getBill must also price customer-owned payer accounts and Azure costs.

### Customer data separation

By default, all customers' data shares one set of storage areas, divided by customer. AWS Lake
Formation permissions and Quick Sight row-level security stop anyone from seeing another
customer's data. A customer that requires stronger separation gets a dedicated AWS account, which
runs the same components with its own storage and its own encryption key.

## Security and compliance

- getBill is designed to the NIST SP 800-53 Revision 5 Moderate controls. FPT is not seeking a
  formal FedRAMP authorization yet, but the Moderate baseline keeps that path open.
- Every storage area is encrypted with keys in AWS KMS, and every access is recorded in AWS
  CloudTrail.
- People sign in through their organization's identity provider, and getBill keeps no passwords of
  its own.
- Issued bills are locked with S3 Object Lock, so nobody can change or delete them during their
  retention period.
- The GovCloud version must address two known limits. AWS Data Exports does not run in GovCloud, so
  billing files must be copied in from the commercial partition. Some Quick Sight features differ
  in GovCloud.
- Questions C7 to C15 in the [requirements questionnaire](getbill-pipeline-questions.md) ask the
  product owner about government customers, Controlled Unclassified Information, FIPS 140
  encryption, Section 508 accessibility and limits on who may see the data. Their answers may
  raise this target.

## Replacing the Excel and VBA processing

**Proposed:** getBill replaces the current Excel and VBA processing in four steps, so that no
customer's bill changes by surprise.

1. **List every step the workbooks and macros perform today**, such as filtering, lookups, price
   changes and totals, together with the reports each step feeds.
2. **Rebuild each step in getBill**, in the transformation, reconciliation or reporting component.
3. **Run both side by side for at least two billing months**, and compare every customer's totals
   between the old workbooks and getBill.
4. **Retire each workbook and macro** once its results match, and keep the comparison as evidence.

## Relationship to the current alpha

The current getBill alpha is a command-line tool that converts billing files in S3 into Excel
workbooks. It is a prototype for parts of this design:

- Its Excel converter becomes the Excel writer in the bills and reports component.
- Its sign-in with two AWS profiles informs how getBill reaches source and destination accounts.
- The [engineering note](getbill-alpha-gap-analysis.md) lists the alpha's 21 known limitations.
  Most of them are closed by the components above.

## Open questions

1. Who owns the Azure billing accounts, and which Microsoft agreement each customer has, such as an
   Enterprise Agreement or a Microsoft Customer Agreement? The available Azure exports depend on
   the agreement type.
2. Which identity providers will customers sign in with?
3. Which reports, and which Excel and VBA steps, exist today?
4. How often is each customer billed, and by which day of the month must a bill be issued?
5. Who at FPT approves a bill before it is released to a customer?
6. Which currencies and taxes must bills handle?
7. How long must raw data, bills and audit records be kept?
8. What counts as unusual spending, and who receives each kind of alert?
9. Will any customer need Azure Government or Google Cloud's government services?

## References

- [Requirements questionnaire](getbill-pipeline-questions.md)
- [Engineering note on the alpha's limitations](getbill-alpha-gap-analysis.md)
- [Restart guide](getbill-restart-guide.md)
- [FinOps Framework](https://www.finops.org/framework/)
- [FOCUS specification](https://focus.finops.org/)
- [Cloud Intelligence Dashboards: Data Exports](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/data-exports.html)
- [Cloud Intelligence Dashboards: FOCUS Dashboard](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/focus-dashboard.html)
- [AWS GovCloud (US) billing](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/usage-and-payment.html)
- [Amazon Quick in AWS GovCloud (US)](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/govcloud-aqs.html)
- [Microsoft Cost Management FOCUS 1.2](https://techcommunity.microsoft.com/blog/finopsblog/focus-1-2-in-microsoft-cost-management-unified-multi-cloud-multi-currency-report/4423852)

<!-- document-footer -->
---

_Internal use only. Last modified: 2026-11-19 08:28 EST. Modified by: mbitar._
<!-- /document-footer -->
