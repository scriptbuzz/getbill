"""Build docs/getbill-aws-architecture.svg from the official AWS, Azure and Google Cloud icons.

The diagram shows how the planned getBill platform in AWS collects the daily billing exports from
customer accounts in AWS, Microsoft Azure and Google Cloud. Each icon is embedded as a base64 data
URI inside an <image> element, so the ids and CSS classes inside one icon can never clash with
another icon or with the diagram itself.

The icon packages are not kept in this repository. Download them from the official pages and unzip
each one into its own folder under one icons folder outside the repository:

    <icons>/aws     https://aws.amazon.com/architecture/icons/ (Icon-package_07312026)
    <icons>/azure   https://learn.microsoft.com/azure/architecture/icons/ (Azure_Public_Service_Icons V25)
    <icons>/gcp     https://cloud.google.com/icons (core products icons)

A newer package may use other folder names. If so, update PATHS below.

    python3 -I scripts/build_architecture_diagram.py <icons> docs/getbill-aws-architecture.svg

The script writes the date, the time and the getBill version into the stamp and the footer. After
you build the diagram, open it in a browser and check that no text is clipped or overlapping.
The script uses only the Python standard library.
"""
import base64
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stamp_docs  # noqa: E402

if len(sys.argv) != 3:
    raise SystemExit("Usage: python3 -I scripts/build_architecture_diagram.py <icons folder> <output.svg>")
ICONS = Path(sys.argv[1])
OUT = Path(sys.argv[2])
A = ICONS / "aws/Architecture-Service-Icons_07312026"
R = ICONS / "aws/Resource-Icons_07312026"
G = ICONS / "aws/Architecture-Group-Icons_07312026"
Z = ICONS / "azure/Azure_Public_Service_Icons/Icons"
GC = ICONS / "gcp/Unique Icons"

PATHS = {
    "orgs": A / "Arch_Management-Tools/48/Arch_AWS-Organizations_48.svg",
    "abc": A / "Arch_Cloud-Financial-Management/48/Arch_AWS-Billing-Conductor_48.svg",
    "cur": A / "Arch_Cloud-Financial-Management/48/Arch_AWS-Cost-and-Usage-Report_48.svg",
    "s3": A / "Arch_Storage/48/Arch_Amazon-Simple-Storage-Service_48.svg",
    "lambda": A / "Arch_Compute/48/Arch_AWS-Lambda_48.svg",
    "glue": A / "Arch_Analytics/48/Arch_AWS-Glue_48.svg",
    "athena": A / "Arch_Analytics/48/Arch_Amazon-Athena_48.svg",
    "catalog": R / "Res_Analytics/Res_AWS-Glue_Data-Catalog_48.svg",
    "sfn": A / "Arch_Application-Integration/48/Arch_AWS-Step-Functions_48.svg",
    "eb": A / "Arch_Application-Integration/48/Arch_Amazon-EventBridge_48.svg",
    "quick": A / "Arch_Business-Applications/48/Arch_Amazon-Quick_48.svg",
    "sns": A / "Arch_Application-Integration/48/Arch_Amazon-Simple-Notification-Service_48.svg",
    "ses": A / "Arch_Business-Applications/48/Arch_Amazon-Simple-Email-Service_48.svg",
    "secrets": A / "Arch_Security-Identity/48/Arch_AWS-Secrets-Manager_48.svg",
    "ssm": A / "Arch_Management-Tools/48/Arch_AWS-Systems-Manager_48.svg",
    "ddb": A / "Arch_Databases/48/Arch_Amazon-DynamoDB_48.svg",
    "kms": A / "Arch_Security-Identity/48/Arch_AWS-Key-Management-Service_48.svg",
    "trail": A / "Arch_Management-Tools/48/Arch_AWS-CloudTrail_48.svg",
    "iam": A / "Arch_Security-Identity/48/Arch_AWS-Identity-and-Access-Management_48.svg",
    "users": R / "Res_General-Icons/Res_48_Light/Res_Users_48_Light.svg",
    "cloud": G / "AWS-Cloud-logo_32.svg",
    "account": G / "AWS-Account_32.svg",
    "az_export": Z / "other/00913-icon-service-Cost-Export.svg",
    "az_cost": Z / "general/10019-icon-service-Cost-Management.svg",
    "az_storage": Z / "storage/10086-icon-service-Storage-Accounts.svg",
    "az_app": Z / "identity/10232-icon-service-App-Registrations.svg",
    "bq": GC / "BigQuery/SVG/BigQuery-512-color.svg",
}

FONT = "'Amazon Ember', 'Helvetica Neue', Helvetica, Arial, sans-serif"
W, H = 1760, 1500
INK = "#232F3E"
GREY = "#545B64"
LINE = "#545B64"


def data_uri(key):
    raw = PATHS[key].read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw)
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    raw = re.sub(r"<title>.*?</title>", "", raw, flags=re.S)
    return "data:image/svg+xml;base64," + base64.b64encode(raw.strip().encode()).decode()


out = []


def add(s):
    out.append(s)


def text(x, y, lines, size=13, weight="400", anchor="middle", fill=INK, cls="label", italic=False):
    if isinstance(lines, str):
        lines = [lines]
    style = ' font-style="italic"' if italic else ""
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else round(size * 1.25, 1)}">{escape(l)}</tspan>'
        for i, l in enumerate(lines)
    )
    add(f'<text class="{cls}" x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}" fill="{fill}"{style}>{spans}</text>')


def icon(key, cx, cy, label, size=48):
    add(f'<image href="{data_uri(key)}" x="{cx - size / 2}" y="{cy - size / 2}" '
        f'width="{size}" height="{size}"/>')
    if label:
        text(cx, cy + size / 2 + 16, label, size=12.5)


def group(x, y, w, h, title, color, key=None, dashed=False, sub=None):
    dash = ' stroke-dasharray="6 4"' if dashed else ""
    add(f'<rect class="group" x="{x}" y="{y}" width="{w}" height="{h}" fill="none" '
        f'stroke="{color}" stroke-width="1.5"{dash}/>')
    tx = x + 12
    if key:
        add(f'<image href="{data_uri(key)}" x="{x}" y="{y}" width="32" height="32"/>')
        tx = x + 42
    text(tx, y + 21, title, size=14, weight="700", anchor="start", fill=INK, cls="gtitle")
    if sub:
        text(tx, y + 40, sub, size=12, anchor="start", fill=GREY, cls="gsub")


def arrow(points, dashed=False, color=LINE):
    d = "M " + " L ".join(f"{x} {y}" for x, y in points)
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#arrow)"/>')


def badge(n, cx, cy):
    add(f'<g class="badge"><circle cx="{cx}" cy="{cy}" r="11" fill="{INK}"/>'
        f'<text x="{cx}" y="{cy + 4.5}" font-size="13" font-weight="700" text-anchor="middle" '
        f'fill="#FFFFFF">{n}</text></g>')


def pill(x, y, w, h, label, fill, ink):
    add(f'<rect class="pill" x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{fill}"/>')
    text(x + w / 2, y + h / 2 + 4.5, label, size=12, weight="700", fill=ink, cls="pilltext")


stamp = stamp_docs.now_text()
version = stamp_docs.current_version()

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="{FONT}" role="img" aria-labelledby="title desc">')
add('<title id="title">getBill: how billing data is collected from AWS, Azure and Google Cloud</title>')
add('<desc id="desc">The architecture shows how getBill copies the daily billing exports of AWS, '
    'Microsoft Azure and Google Cloud customer accounts into a data lake in AWS, converts them to '
    'FOCUS 1.2 and shows them in Amazon Quick dashboards.</desc>')
add('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    f'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="{LINE}"/></marker></defs>')
add(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

text(40, 44, "getBill: how billing data is collected from AWS, Azure and Google Cloud",
     size=26, weight="700", anchor="start", cls="title")
add(f'<text id="last-modified" x="40" y="70" font-size="13" font-style="italic" fill="{GREY}">'
    f'Last modified: {stamp}. Version: {version}.</text>')
text(40, 94, "Each cloud writes a daily billing export inside the customer's own account. getBill copies "
     "the exports into its data lake in AWS, converts them to one format, and shows them in dashboards.",
     size=14, anchor="start", fill=GREY, cls="lead")

# ---------- Left column: customer clouds ----------
LX, LW = 30, 500
TOP = 120

# AWS customer side
group(LX, TOP, LW, 430, "AWS: payer accounts that hold the customers' bills", INK, key="cloud")
# FPT payer account
group(LX + 16, TOP + 48, LW - 32, 190, "FPT payer account (reseller)", "#E7157B", key="account")
Y1 = TOP + 120
icon("orgs", 105, Y1, ["AWS Organizations", "(customer accounts)"])
icon("abc", 225, Y1, ["AWS Billing", "Conductor"])
icon("cur", 345, Y1, ["AWS Data", "Exports"])
badge(1, 460, Y1 - 18)
# Customer-owned payer account
group(LX + 16, TOP + 250, LW - 32, 170, "Customer's own payer account", "#E7157B", key="account",
      sub="This account is used when a customer pays AWS directly.")
Y2 = TOP + 342
icon("iam", 140, Y2, ["IAM role (used when the", "customer keeps its files)"])
icon("cur", 345, Y2, ["AWS Data", "Exports"])
badge(2, 460, Y2 - 18)

# Azure
AZ = TOP + 450
group(LX, AZ, LW, 250, "Microsoft Azure: customer billing account", "#0078D4")
YA = AZ + 95
icon("az_export", 105, YA, ["Cost Management", "FOCUS export"], size=44)
icon("az_storage", 465, YA, ["Storage account", "(export files)"], size=44)
arrow([(131, YA), (439, YA)])
badge(3, 285, YA - 18)
icon("az_app", 285, AZ + 190, ["Entra ID application", "(read-only access)"], size=40)

# Google Cloud
GZ = AZ + 270
group(LX, GZ, LW, 200, "Google Cloud: customer billing account", "#4285F4")
pill(LX + LW - 128, GZ + 8, 116, 24, "Later release", "#FEF7E0", "#7A5300")
YG = GZ + 100
add(f'<rect class="box" x="58" y="{YG - 26}" width="150" height="52" rx="6" fill="#F1F3F4" stroke="#4285F4"/>')
text(133, YG - 4, ["Cloud Billing", "export"], size=12.5, cls="boxtext")
icon("bq", 465, YG, ["BigQuery dataset", "(billing tables)"], size=48)
arrow([(208, YG), (439, YG)])

# ---------- Middle: getBill account ----------
MX, MY, MW, MH = 580, TOP, 900, 960
group(MX, MY, MW, MH, "getBill account in FPT's AWS organization", INK, key="account",
      sub="This account holds the data lake, the processing jobs and the dashboards.")
MAIN = YA  # main flow row lines up with the Azure row

# Ingestion
icon("lambda", 690, MAIN, ["AWS Lambda", "(Azure copy)"])
icon("glue", 690, YG, ["AWS Glue job", "(BigQuery connector)"])
arrow([(491, MAIN), (664, MAIN)])
badge(4, 600, MAIN - 18)
arrow([(491, YG), (664, YG)])
badge(5, 600, YG - 18)

# Main flow
RAW, ETL, CUR, ATH, QK = 840, 990, 1140, 1290, 1420
icon("s3", RAW, MAIN, ["Amazon S3", "raw zone"])
icon("glue", ETL, MAIN, ["AWS Glue ETL", "(convert to FOCUS)"])
icon("s3", CUR, MAIN, ["Amazon S3 normalized", "and curated zones"])
icon("athena", ATH, MAIN, ["Amazon Athena", "(SQL views)"])
icon("quick", QK, MAIN, ["Amazon Quick", "dashboards"])
arrow([(716, MAIN), (814, MAIN)])
arrow([(716, YG), (RAW, YG), (RAW, MAIN + 70)])
# AWS Data Exports delivers straight into the raw zone
add(f'<path d="M 371 {Y1} L 548 {Y1} L 548 {Y2} L 371 {Y2}" fill="none" stroke="{LINE}" stroke-width="1.6"/>')
arrow([(548, (Y1 + Y2) / 2), (RAW, (Y1 + Y2) / 2), (RAW, MAIN - 26)])
text(700, (Y1 + Y2) / 2 + 22, ["Direct delivery by", "AWS Data Exports"], size=12.5, fill=GREY, cls="note")
arrow([(866, MAIN), (964, MAIN)])
arrow([(1016, MAIN), (1114, MAIN)])
arrow([(1166, MAIN), (1264, MAIN)])
arrow([(1316, MAIN), (1394, MAIN)])

# Orchestration above ETL
EBY, SFY = MY + 110, MY + 260
icon("eb", ETL, EBY, ["Amazon EventBridge", "Scheduler"])
icon("sfn", ETL, SFY, ["AWS Step Functions"])
arrow([(ETL, EBY + 66), (ETL, SFY - 26)])
arrow([(ETL, SFY + 44), (ETL, MAIN - 26)])
badge(6, ETL + 22, MAIN - 50)
icon("catalog", ATH, SFY, ["AWS Glue", "Data Catalog"])
arrow([(CUR, MAIN - 26), (CUR, SFY), (ATH - 26, SFY)], dashed=True)
arrow([(ATH, SFY + 66), (ATH, MAIN - 26)], dashed=True)
badge(7, ATH + 22, MAIN - 50)
badge(8, QK - 22, MAIN - 50)

# Shared services
SX, SY, SW, SH = 910, MY + 645, 550, 295
group(SX, SY, SW, SH, "Shared services", GREY, dashed=True)
cols = [SX + 70, SX + 205, SX + 340, SX + 475]
r1, r2 = SY + 85, SY + 210
icon("secrets", cols[0], r1, ["AWS Secrets", "Manager"], size=44)
icon("ssm", cols[1], r1, ["Systems Manager", "Parameter Store"], size=44)
icon("ddb", cols[2], r1, ["Amazon DynamoDB", "(customer registry)"], size=44)
icon("iam", cols[3], r1, ["AWS IAM", "(roles)"], size=44)
icon("kms", cols[0], r2, ["AWS KMS", "(encryption keys)"], size=44)
icon("trail", cols[1], r2, ["AWS CloudTrail", "(access records)"], size=44)
icon("sns", cols[2], r2, ["Amazon SNS", "(alerts)"], size=44)
icon("ses", cols[3], r2, ["Amazon SES", "(alert emails)"], size=44)
badge(9, SX + SW - 20, SY + 18)

# ---------- Right: users ----------
UX = 1620
users = [(MAIN - 150, ["FPT FinOps team"]), (MAIN, ["Customer finance", "team"]),
         (MAIN + 150, ["Customer engineers"])]
for uy, lab in users:
    icon("users", UX, uy, lab)
add(f'<path d="M 1446 {MAIN} L 1530 {MAIN}" fill="none" stroke="{LINE}" stroke-width="1.6"/>')
add(f'<path d="M 1530 {MAIN - 150} L 1530 {MAIN + 150}" fill="none" stroke="{LINE}" stroke-width="1.6"/>')
for uy, _ in users:
    arrow([(1530, uy), (1594, uy)])
text(UX, MAIN - 220, "People who use getBill", size=13, weight="700", cls="label")

# ---------- Legend ----------
LY = MY + MH + 40
text(40, LY, "How the data moves, step by step", size=17, weight="700", anchor="start", cls="lhead")
steps = [
    ("1", "Every day, AWS Data Exports in each of FPT's payer accounts writes a CUR 2.0 export and a FOCUS "
          "1.2 export straight into the raw zone of getBill's data lake. A bucket policy lets Data Exports "
          "write there, so getBill holds no passwords or keys for the payer accounts. AWS Billing Conductor "
          "groups the accounts of each customer and sets the price that FPT charges."),
    ("2", "A customer that pays AWS directly sends its exports to getBill in the same way. Instead, the "
          "customer can keep the exports in its own bucket and let getBill read them through an IAM role "
          "that requires an external ID, a value shared only between FPT and that customer."),
    ("3", "Every day, Azure Cost Management writes a FOCUS export to a storage account in the customer's "
          "Azure tenant."),
    ("4", "An EventBridge schedule starts a Lambda function that copies the new files into the raw zone. "
          "The function signs in with an Entra ID application. In the proposed design, the application "
          "trusts a signed token from AWS, so no secret is stored. Otherwise, the function uses a "
          "certificate that is kept in Secrets Manager."),
    ("5", "An AWS Glue job uses the Google BigQuery connector to read the customer's billing export "
          "tables and writes them to the raw zone. It signs in through Google's Workload Identity "
          "Federation, which trusts getBill's AWS role, so no key file is stored. Google Cloud support is "
          "planned for a later release."),
    ("6", "Step Functions runs AWS Glue ETL jobs. They convert every source to FOCUS 1.2 in the "
          "normalized zone, then map the costs to customers, add FPT's resale price, and write the approved "
          "data to the curated zone. Issued bills go to a fourth zone, the output zone, which this diagram "
          "does not show."),
    ("7", "The Glue Data Catalog holds the table definitions, and Athena views join and summarize the "
          "curated data."),
    ("8", "Amazon Quick dashboards query the Athena views. Row-level security in Amazon Quick shows each "
          "customer only their own costs."),
    ("9", "SNS and SES send budget and anomaly alerts. DynamoDB lists every customer and cloud account, "
          "Secrets Manager holds any certificate that a connection still needs, Parameter Store holds the settings of each connection, IAM roles give each job only the access "
          "it needs, KMS encrypts the stored data, and CloudTrail records every access."),
]


def wrap(s, width):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


colx = [40, 900]
y_col = [LY + 30, LY + 30]
for i, (n, s) in enumerate(steps):
    c = 0 if i < 5 else 1
    lines = wrap(s, 112)
    badge(n, colx[c] + 11, y_col[c] - 4)
    text(colx[c] + 32, y_col[c], lines, size=13, anchor="start", cls="step")
    y_col[c] += len(lines) * 16.25 + 14

src_y = max(y_col) + 14
text(40, src_y, ["Sources: AWS Cloud Financial Management blog, \"Automating multi-cloud cost management at "
                 "scale: A2A's FinOps platform powered by AWS\"; AWS Data Exports and AWS Billing Conductor "
                 "documentation;",
                 "Microsoft Cost Management exports documentation; Google Cloud Billing export to BigQuery "
                 "documentation. Icons are the official AWS, Microsoft Azure and Google Cloud icon sets."],
     size=12, anchor="start", fill=GREY, cls="sources")
add(f'<text id="document-footer" x="40" y="{src_y + 48}" font-size="12" fill="{GREY}">'
    f'{stamp_docs.footer_sentence(stamp, version)}</text>')
add("</svg>")

svg = "\n".join(out)
svg = re.sub(r'height="1500" viewBox="0 0 1760 1500"',
             f'height="{src_y + 70}" viewBox="0 0 {W} {src_y + 70}"', svg, count=1)
svg = svg.replace(f'<rect width="{W}" height="{H}"', f'<rect width="{W}" height="{src_y + 70}"', 1)
OUT.write_text(svg + "\n", encoding="utf-8")
print(f"Wrote {OUT} ({len(svg) // 1024} KB).")
