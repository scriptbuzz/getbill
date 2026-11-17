"""Generate a synthetic AWS Cost and Usage Report (CUR 2.0) file for testing, as CSV or Parquet.

The file follows the CUR 2.0 column names from AWS Data Exports and includes only the
unblended cost columns (no blended cost or blended rate). The rows describe hourly usage
of big data services (EMR, EMR Serverless, Glue, Athena, Redshift, Kinesis, Firehose,
MSK, OpenSearch, and S3 data lake storage) and Amazon Bedrock (on-demand and batch
inference, embeddings, guardrails, provisioned throughput, and model customization).
Monthly tax lines and a few credit lines are added at the end.

All account IDs, prices, and resource names are made up. Prices are close to public
on-demand prices but are not exact, so do not use the file for cost estimates.

CSV output uses only the Python standard library, so it runs without installing anything.
Parquet output, chosen by an output name that ends in .parquet, needs the pyarrow library:

    python3 scripts/generate_cur2_sample.py --rows 10000 --month 2026-10 --output samples/cur2.csv
    python3 scripts/generate_cur2_sample.py --output samples/cur2-export-00001.snappy.parquet
"""

from __future__ import annotations

import argparse
import calendar
import csv
import json
import random
import string
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

COLUMNS = [
    "bill_bill_type", "bill_billing_entity", "bill_billing_period_end_date",
    "bill_billing_period_start_date", "bill_invoice_id", "bill_invoicing_entity",
    "bill_payer_account_id", "bill_payer_account_name", "cost_category", "discount",
    "identity_line_item_id", "identity_time_interval", "line_item_availability_zone",
    "line_item_currency_code", "line_item_legal_entity", "line_item_line_item_description",
    "line_item_line_item_type", "line_item_net_unblended_cost", "line_item_net_unblended_rate",
    "line_item_normalization_factor", "line_item_normalized_usage_amount", "line_item_operation",
    "line_item_product_code", "line_item_resource_id", "line_item_tax_type",
    "line_item_unblended_cost", "line_item_unblended_rate", "line_item_usage_account_id",
    "line_item_usage_account_name", "line_item_usage_amount", "line_item_usage_end_date",
    "line_item_usage_start_date", "line_item_usage_type", "pricing_currency",
    "pricing_public_on_demand_cost", "pricing_public_on_demand_rate", "pricing_purchase_option",
    "pricing_rate_code", "pricing_rate_id", "pricing_term", "pricing_unit", "product",
    "product_fee_code", "product_fee_description", "product_from_location",
    "product_instance_family", "product_instance_type", "product_location",
    "product_location_type", "product_operation", "product_pricing_unit",
    "product_product_family", "product_region_code", "product_servicecode", "product_sku",
    "product_to_location", "product_usagetype", "resource_tags",
]

PAYER = ("111122223333", "Example Holdings Payer")
# The last account ID starts with 0 on purpose, to test that IDs stay text in Excel.
ACCOUNTS = [
    ("444455556666", "data-platform-prod", "data-engineering", "prod"),
    ("777788889999", "analytics-dev", "analytics", "dev"),
    ("012345678901", "genai-applications", "genai", "prod"),
]
REGIONS = {
    "us-east-1": ("USE1", "US East (N. Virginia)", ["us-east-1a", "us-east-1b", "us-east-1c"]),
    "us-west-2": ("USW2", "US West (Oregon)", ["us-west-2a", "us-west-2b"]),
    "eu-west-1": ("EU", "EU (Ireland)", ["eu-west-1a", "eu-west-1b"]),
}

# Each entry is one kind of usage line. "usage" is the (low, high) range of the hourly
# usage amount, "weight" is how often the line appears, and "account" limits which
# accounts use it (an index into ACCOUNTS).
CATALOG: List[Dict] = [
    # ---------------- Big data services
    dict(code="ElasticMapReduce", service="Amazon Elastic MapReduce", family="Elastic Map Reduce Instance",
         usage_type="ElasticMapReduce-Instance:m5.2xlarge", operation="RunInstances", unit="Hrs", rate=0.096,
         usage=(1, 20), weight=8, instance="m5.2xlarge", az=True, resource="emr",
         description="$0.096 per hour for EMR m5.2xlarge"),
    dict(code="AmazonEC2", service="Amazon Elastic Compute Cloud", family="Compute Instance",
         usage_type="BoxUsage:m5.2xlarge", operation="RunInstances", unit="Hrs", rate=0.384,
         usage=(1, 20), weight=8, instance="m5.2xlarge", az=True, resource="ec2",
         description="$0.384 per On Demand Linux m5.2xlarge Instance Hour (EMR cluster node)"),
    dict(code="ElasticMapReduce", service="Amazon Elastic MapReduce", family="EMR Serverless",
         usage_type="EMR-SERVERLESS-vCPUHours", operation="Worker", unit="vCPU-Hours", rate=0.052624,
         usage=(4, 400), weight=5, resource="emr-serverless",
         description="$0.052624 per vCPU-hour for EMR Serverless"),
    dict(code="ElasticMapReduce", service="Amazon Elastic MapReduce", family="EMR Serverless",
         usage_type="EMR-SERVERLESS-MemoryGBHours", operation="Worker", unit="GB-Hours", rate=0.0057785,
         usage=(16, 1600), weight=5, resource="emr-serverless",
         description="$0.0057785 per GB-hour for EMR Serverless memory"),
    dict(code="AWSGlue", service="AWS Glue", family="AWS Glue",
         usage_type="ETL-DPU-Hour", operation="Jobrun", unit="DPU-Hour", rate=0.44,
         usage=(0.5, 60), weight=9, resource="glue-job",
         description="$0.44 per DPU-Hour for Glue ETL jobs"),
    dict(code="AWSGlue", service="AWS Glue", family="AWS Glue",
         usage_type="Crawler-DPU-Hour", operation="CrawlerRun", unit="DPU-Hour", rate=0.44,
         usage=(0.1, 4), weight=3, resource="glue-crawler",
         description="$0.44 per DPU-Hour for Glue crawlers"),
    dict(code="AWSGlue", service="AWS Glue", family="Data Catalog Requests",
         usage_type="Catalog-Request", operation="Request", unit="Requests", rate=0.000001,
         usage=(1000, 900000), weight=3, integer=True,
         description="$1.00 per million Glue Data Catalog requests"),
    dict(code="AmazonAthena", service="Amazon Athena", family="Athena Queries",
         usage_type="DataScannedInTB", operation="RunQuery", unit="Terabytes", rate=5.0,
         usage=(0.001, 2.5), weight=9, resource="athena-workgroup",
         description="$5.00 per TB of data scanned by Athena queries"),
    dict(code="AmazonRedshift", service="Amazon Redshift", family="Compute Instance",
         usage_type="Node:ra3.4xlarge", operation="RunComputeNode:0001", unit="Hrs", rate=3.26,
         usage=(2, 4), weight=6, instance="ra3.4xlarge", integer=True, resource="redshift",
         description="$3.26 per RA3 4XL node-hour"),
    dict(code="AmazonRedshift", service="Amazon Redshift", family="Redshift Managed Storage",
         usage_type="RMS:ra3", operation="RunComputeNode:0001", unit="GB-Mo", rate=0.024,
         usage=(50, 900), weight=3, resource="redshift",
         description="$0.024 per GB-month of Redshift managed storage"),
    dict(code="AmazonRedshift", service="Amazon Redshift", family="Redshift Serverless",
         usage_type="RedshiftServerless:Usage", operation="ServerlessUsage", unit="RPU-Hr", rate=0.375,
         usage=(8, 256), weight=4, resource="redshift-serverless", account=[1],
         description="$0.375 per RPU-hour for Redshift Serverless"),
    dict(code="AmazonKinesis", service="Amazon Kinesis", family="Kinesis Streams",
         usage_type="Storage-ShardHour", operation="shardHourStorage", unit="ShardHour", rate=0.015,
         usage=(4, 64), weight=5, integer=True, resource="kinesis",
         description="$0.015 per Kinesis shard hour"),
    dict(code="AmazonKinesis", service="Amazon Kinesis", family="Kinesis Streams",
         usage_type="PutRequestPayloadUnits", operation="PutRecord", unit="PutRequestPayloadUnits",
         rate=0.000000014, usage=(1_000_000, 90_000_000), weight=4, integer=True, resource="kinesis",
         description="$0.014 per 1,000,000 PUT payload units"),
    dict(code="AmazonKinesisFirehose", service="Amazon Kinesis Firehose", family="Kinesis Firehose",
         usage_type="BilledBytes", operation="PutRecordBatch", unit="GB", rate=0.029,
         usage=(1, 400), weight=4, resource="firehose",
         description="$0.029 per GB of data ingested by Firehose"),
    dict(code="AmazonMSK", service="Amazon Managed Streaming for Apache Kafka", family="Managed Streaming for Apache Kafka (MSK)",
         usage_type="Kafka.m5.large", operation="RunBroker", unit="Hrs", rate=0.21,
         usage=(3, 6), weight=4, instance="kafka.m5.large", integer=True, az=True, resource="msk",
         description="$0.21 per Kafka broker hour (kafka.m5.large)"),
    dict(code="AmazonMSK", service="Amazon Managed Streaming for Apache Kafka", family="Storage",
         usage_type="Kafka.Storage.GP2", operation="RunBroker", unit="GB-Mo", rate=0.10,
         usage=(1, 40), weight=2, resource="msk",
         description="$0.10 per GB-month of MSK broker storage"),
    dict(code="AmazonES", service="Amazon OpenSearch Service", family="Amazon OpenSearch Service Instance",
         usage_type="ESInstance:r6g.large", operation="ESDomain", unit="Hrs", rate=0.167,
         usage=(2, 6), weight=3, instance="r6g.large.search", integer=True, resource="opensearch",
         description="$0.167 per hour for r6g.large.search instances"),
    dict(code="AmazonS3", service="Amazon Simple Storage Service", family="Storage",
         usage_type="TimedStorage-ByteHrs", operation="StandardStorage", unit="GB-Mo", rate=0.023,
         usage=(5, 900), weight=7, resource="s3",
         description="$0.023 per GB-month of S3 Standard storage (data lake)"),
    dict(code="AmazonS3", service="Amazon Simple Storage Service", family="API Request",
         usage_type="Requests-Tier1", operation="PutObject", unit="Requests", rate=0.000005,
         usage=(1000, 500000), weight=5, integer=True, resource="s3",
         description="$0.005 per 1,000 PUT, COPY, POST, or LIST requests"),
    dict(code="AmazonS3", service="Amazon Simple Storage Service", family="API Request",
         usage_type="Requests-Tier2", operation="GetObject", unit="Requests", rate=0.0000004,
         usage=(10000, 5000000), weight=5, integer=True, resource="s3",
         description="$0.0004 per 1,000 GET and all other requests"),
    # ---------------- Amazon Bedrock
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="NovaPro-input-tokens", operation="InvokeModelInference", unit="1K tokens", rate=0.0008,
         usage=(50, 40000), weight=8, model="amazon.nova-pro-v1:0", resource="bedrock-model", account=[2, 1],
         description="$0.0008 per 1K input tokens for Nova Pro"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="NovaPro-output-tokens", operation="InvokeModelInference", unit="1K tokens", rate=0.0032,
         usage=(10, 8000), weight=8, model="amazon.nova-pro-v1:0", resource="bedrock-model", account=[2, 1],
         description="$0.0032 per 1K output tokens for Nova Pro"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="NovaLite-input-tokens", operation="InvokeModelInference", unit="1K tokens", rate=0.00006,
         usage=(100, 90000), weight=6, model="amazon.nova-lite-v1:0", resource="bedrock-model", account=[2],
         description="$0.00006 per 1K input tokens for Nova Lite"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="NovaLite-output-tokens", operation="InvokeModelInference", unit="1K tokens", rate=0.00024,
         usage=(20, 18000), weight=6, model="amazon.nova-lite-v1:0", resource="bedrock-model", account=[2],
         description="$0.00024 per 1K output tokens for Nova Lite"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="NovaLite-batch-input-tokens", operation="InvokeModelBatchInference", unit="1K tokens",
         rate=0.00003, usage=(10000, 900000), weight=2, model="amazon.nova-lite-v1:0", resource="bedrock-model",
         account=[0], description="$0.00003 per 1K input tokens for Nova Lite batch inference"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="Llama3-1-70B-input-tokens", operation="InvokeModelInference", unit="1K tokens", rate=0.00072,
         usage=(50, 20000), weight=4, model="meta.llama3-1-70b-instruct-v1:0", resource="bedrock-model",
         account=[1, 2], description="$0.00072 per 1K input tokens for Llama 3.1 70B Instruct"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="Llama3-1-70B-output-tokens", operation="InvokeModelInference", unit="1K tokens", rate=0.00072,
         usage=(10, 5000), weight=4, model="meta.llama3-1-70b-instruct-v1:0", resource="bedrock-model",
         account=[1, 2], description="$0.00072 per 1K output tokens for Llama 3.1 70B Instruct"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="MistralLarge-input-tokens", operation="InvokeModelInference", unit="1K tokens", rate=0.002,
         usage=(20, 6000), weight=2, model="mistral.mistral-large-2407-v1:0", resource="bedrock-model",
         account=[2], description="$0.002 per 1K input tokens for Mistral Large"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="TitanEmbedTextV2-input-tokens", operation="InvokeModelInference", unit="1K tokens",
         rate=0.00002, usage=(1000, 400000), weight=5, model="amazon.titan-embed-text-v2:0",
         resource="bedrock-model", account=[2, 0],
         description="$0.00002 per 1K input tokens for Titan Text Embeddings V2 (knowledge base ingestion)"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="Guardrails-ContentPolicy-TextUnits", operation="ApplyGuardrail", unit="1K text units",
         rate=0.15, usage=(1, 120), weight=3, resource="bedrock-guardrail", account=[2],
         description="$0.15 per 1K text units for guardrail content filters"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="ProvisionedThroughput-NovaPro-ModelUnits", operation="ProvisionedThroughput", unit="Hrs",
         rate=22.0, usage=(1, 2), weight=2, integer=True, model="amazon.nova-pro-v1:0",
         resource="bedrock-provisioned", account=[2],
         description="$22.00 per model unit hour of provisioned throughput for Nova Pro"),
    dict(code="AmazonBedrock", service="Amazon Bedrock", family="Amazon Bedrock",
         usage_type="NovaMicro-Customization-Training-tokens", operation="ModelCustomization", unit="1K tokens",
         rate=0.001, usage=(1000, 60000), weight=1, model="amazon.nova-micro-v1:0", resource="bedrock-custom",
         account=[2], description="$0.001 per 1K tokens for Nova Micro fine-tuning"),
]

TAGS = {
    "data-engineering": ["ingestion", "lakehouse", "streaming"],
    "analytics": ["bi-dashboards", "ad-hoc-sql", "forecasting"],
    "genai": ["support-assistant", "document-search", "content-summaries"],
}


def random_token(rng: random.Random, length: int, alphabet: str = string.ascii_uppercase + string.digits) -> str:
    return "".join(rng.choice(alphabet) for _ in range(length))


def fmt_number(value: float) -> str:
    """Format a number the way CUR CSV files do: plain decimals, no exponent, no trailing zeros."""
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def fmt_time(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def resource_id(rng: random.Random, kind: Optional[str], region: str, account: str, entry: Dict, team: str) -> str:
    project = rng.choice(TAGS[team])
    if kind == "emr":
        return f"arn:aws:elasticmapreduce:{region}:{account}:cluster/j-{random_token(rng, 13)}"
    if kind == "ec2":
        return f"i-0{random_token(rng, 16, '0123456789abcdef')}"
    if kind == "emr-serverless":
        return f"arn:aws:emr-serverless:{region}:{account}:/applications/00f{random_token(rng, 13, '0123456789abcdef')}"
    if kind == "glue-job":
        return f"arn:aws:glue:{region}:{account}:job/{project}-etl"
    if kind == "glue-crawler":
        return f"arn:aws:glue:{region}:{account}:crawler/{project}-crawler"
    if kind == "athena-workgroup":
        return f"arn:aws:athena:{region}:{account}:workgroup/{project}"
    if kind == "redshift":
        return f"arn:aws:redshift:{region}:{account}:cluster:{project}-warehouse"
    if kind == "redshift-serverless":
        return f"arn:aws:redshift-serverless:{region}:{account}:workgroup/{project}"
    if kind == "kinesis":
        return f"arn:aws:kinesis:{region}:{account}:stream/{project}-events"
    if kind == "firehose":
        return f"arn:aws:firehose:{region}:{account}:deliverystream/{project}-to-s3"
    if kind == "msk":
        return f"arn:aws:kafka:{region}:{account}:cluster/{project}-kafka/{random_token(rng, 8, '0123456789abcdef')}"
    if kind == "opensearch":
        return f"arn:aws:es:{region}:{account}:domain/{project}-search"
    if kind == "s3":
        return f"{team}-{project}-datalake-{account}"
    if kind == "bedrock-model":
        return f"arn:aws:bedrock:{region}::foundation-model/{entry['model']}"
    if kind == "bedrock-guardrail":
        return f"arn:aws:bedrock:{region}:{account}:guardrail/{random_token(rng, 12, string.ascii_lowercase + string.digits)}"
    if kind == "bedrock-provisioned":
        return f"arn:aws:bedrock:{region}:{account}:provisioned-model/{random_token(rng, 12, string.ascii_lowercase + string.digits)}"
    if kind == "bedrock-custom":
        return f"arn:aws:bedrock:{region}:{account}:custom-model/{entry['model']}/{project}"
    return ""


class Generator:
    def __init__(self, month: str, seed: int):
        self.rng = random.Random(seed)
        year, number = (int(part) for part in month.split("-"))
        self.start = datetime(year, number, 1, tzinfo=timezone.utc)
        self.end = self.start + timedelta(days=calendar.monthrange(year, number)[1])
        self.hours = int((self.end - self.start).total_seconds() // 3600)
        self.invoice_id = str(self.rng.randint(1_000_000_000, 9_999_999_999))  # Ten-digit invoice number.
        self.skus: Dict[str, str] = {}
        self.rate_ids: Dict[str, str] = {}

    def base_row(self, account) -> Dict[str, str]:
        account_id, account_name, team, _ = account
        return {
            "bill_bill_type": "Anniversary",
            "bill_billing_entity": "AWS",
            "bill_billing_period_end_date": fmt_time(self.end),
            "bill_billing_period_start_date": fmt_time(self.start),
            "bill_invoice_id": self.invoice_id,
            "bill_invoicing_entity": "Amazon Web Services, Inc.",
            "bill_payer_account_id": PAYER[0],
            "bill_payer_account_name": PAYER[1],
            "cost_category": json.dumps({"business_unit": team}),
            "discount": "{}",
            "identity_line_item_id": random_token(self.rng, 52, string.ascii_lowercase + "234567"),
            "line_item_currency_code": "USD",
            "line_item_legal_entity": "Amazon Web Services, Inc.",
            "line_item_usage_account_id": account_id,
            "line_item_usage_account_name": account_name,
            "pricing_currency": "USD",
        }

    def usage_row(self) -> Dict[str, str]:
        rng = self.rng
        entry = rng.choices(CATALOG, weights=[e["weight"] for e in CATALOG])[0]
        account = ACCOUNTS[rng.choice(entry.get("account", [0, 1, 2]))]
        account_id, _, team, env = account
        region = rng.choices(list(REGIONS), weights=[7, 2, 1])[0]
        prefix, location, zones = REGIONS[region]
        hour = self.start + timedelta(hours=rng.randrange(self.hours))
        low, high = entry["usage"]
        amount = rng.randint(int(low), int(high)) if entry.get("integer") else rng.uniform(low, high)
        cost = round(amount * entry["rate"], 10)
        usage_type = f"{prefix}-{entry['usage_type']}"
        sku_key = f"{usage_type}|{entry['operation']}"
        sku = self.skus.setdefault(sku_key, random_token(rng, 16))
        rate_id = self.rate_ids.setdefault(sku_key, str(rng.randint(100_000_000_000, 999_999_999_999)))
        product = {"servicename": entry["service"], "region": region, "usagetype": usage_type}
        if "model" in entry:
            product["model_id"] = entry["model"]
        instance = entry.get("instance", "")

        row = self.base_row(account)
        row.update({
            "identity_time_interval": f"{fmt_time(hour)[:19]}Z/{fmt_time(hour + timedelta(hours=1))[:19]}Z",
            "line_item_availability_zone": rng.choice(zones) if entry.get("az") else "",
            "line_item_line_item_description": f"{entry['description']} in {location}",
            "line_item_line_item_type": "Usage",
            "line_item_net_unblended_cost": fmt_number(cost),
            "line_item_net_unblended_rate": fmt_number(entry["rate"]),
            "line_item_normalization_factor": "8" if instance.endswith("2xlarge") else "",
            "line_item_normalized_usage_amount": fmt_number(amount * 8) if instance.endswith("2xlarge") else "",
            "line_item_operation": entry["operation"],
            "line_item_product_code": entry["code"],
            "line_item_resource_id": resource_id(rng, entry.get("resource"), region, account_id, entry, team),
            "line_item_tax_type": "",
            "line_item_unblended_cost": fmt_number(cost),
            "line_item_unblended_rate": fmt_number(entry["rate"]),
            "line_item_usage_amount": fmt_number(amount),
            "line_item_usage_end_date": fmt_time(hour + timedelta(hours=1)),
            "line_item_usage_start_date": fmt_time(hour),
            "line_item_usage_type": usage_type,
            "pricing_public_on_demand_cost": fmt_number(cost),
            "pricing_public_on_demand_rate": fmt_number(entry["rate"]),
            "pricing_purchase_option": "OnDemand",
            "pricing_rate_code": f"{sku}.JRTCKXETXF.6YS6EN2CT7",
            "pricing_rate_id": rate_id,
            "pricing_term": "OnDemand",
            "pricing_unit": entry["unit"],
            "product": json.dumps(product),
            "product_fee_code": "",
            "product_fee_description": "",
            "product_from_location": "",
            "product_instance_family": instance.split(".")[0] if instance and not instance.startswith("kafka") else "",
            "product_instance_type": instance,
            "product_location": location,
            "product_location_type": "AWS Region",
            "product_operation": entry["operation"],
            "product_pricing_unit": entry["unit"],
            "product_product_family": entry["family"],
            "product_region_code": region,
            "product_servicecode": entry["code"],
            "product_sku": sku,
            "product_to_location": "",
            "product_usagetype": usage_type,
            "resource_tags": json.dumps({
                "user_team": team,
                "user_environment": env,
                "user_project": rng.choice(TAGS[team]),
            }),
        })
        return row

    def adjustment_row(self, account, product_code: str, kind: str, amount: float) -> Dict[str, str]:
        """Build a monthly tax line or a credit line for one account and service."""
        row = {column: "" for column in COLUMNS}
        row.update(self.base_row(account))
        description = "Tax for product code " + product_code if kind == "Tax" else "Promotional credit for data and AI workloads"
        row.update({
            "identity_time_interval": f"{fmt_time(self.start)[:19]}Z/{fmt_time(self.end)[:19]}Z",
            "line_item_line_item_description": description,
            "line_item_line_item_type": kind,
            "line_item_net_unblended_cost": fmt_number(amount),
            "line_item_product_code": product_code,
            "line_item_tax_type": "Sales" if kind == "Tax" else "",
            "line_item_unblended_cost": fmt_number(amount),
            "line_item_usage_amount": "1" if kind == "Tax" else "0",
            "line_item_usage_end_date": fmt_time(self.end),
            "line_item_usage_start_date": fmt_time(self.start),
            "product": json.dumps({"servicename": product_code}),
            "product_servicecode": product_code,
            "resource_tags": "{}",
        })
        return row

    def rows(self, count: int):
        totals: Dict[tuple, float] = defaultdict(float)
        for _ in range(count):
            row = self.usage_row()
            totals[(row["line_item_usage_account_id"], row["line_item_product_code"])] += float(row["line_item_unblended_cost"])
            yield row
        accounts = {account[0]: account for account in ACCOUNTS}
        for (account_id, product_code), total in sorted(totals.items()):
            yield self.adjustment_row(accounts[account_id], product_code, "Tax", round(total * 0.0625, 10))
        for product_code in ("AmazonBedrock", "AmazonAthena"):
            yield self.adjustment_row(ACCOUNTS[2], product_code, "Credit", -round(self.rng.uniform(50, 400), 2))


# Column types for the Parquet version, chosen to match a CUR 2.0 Parquet export:
# costs and amounts are numbers, dates are UTC timestamps, and the four map columns
# hold key-value pairs. Every other column is text.
MAP_COLUMNS = {"cost_category", "discount", "product", "resource_tags"}
TIMESTAMP_COLUMNS = {
    "bill_billing_period_end_date", "bill_billing_period_start_date",
    "line_item_usage_end_date", "line_item_usage_start_date",
}
NUMBER_COLUMNS = {
    "line_item_net_unblended_cost", "line_item_net_unblended_rate", "line_item_normalization_factor",
    "line_item_normalized_usage_amount", "line_item_unblended_cost", "line_item_unblended_rate",
    "line_item_usage_amount", "pricing_public_on_demand_cost", "pricing_public_on_demand_rate",
}


def write_csv(rows, output: Path) -> int:
    written = 0
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, restval="")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            written += 1
    return written


def write_parquet(rows, output: Path) -> int:
    """Write the rows as a Snappy-compressed Parquet file. This needs the pyarrow library."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise SystemExit("Writing Parquet needs the pyarrow library. Install it with: pip install pyarrow")

    values = {column: [] for column in COLUMNS}
    for row in rows:
        for column in COLUMNS:
            text = row.get(column, "")
            if column in MAP_COLUMNS:
                values[column].append([(k, str(v)) for k, v in json.loads(text).items()] if text else None)
            elif column in TIMESTAMP_COLUMNS:
                values[column].append(
                    datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=timezone.utc) if text else None
                )
            elif column in NUMBER_COLUMNS:
                values[column].append(float(text) if text else None)
            else:
                values[column].append(text or None)

    def arrow_type(column):
        if column in MAP_COLUMNS:
            return pa.map_(pa.string(), pa.string())
        if column in TIMESTAMP_COLUMNS:
            return pa.timestamp("ms", tz="UTC")
        if column in NUMBER_COLUMNS:
            return pa.float64()
        return pa.string()

    table = pa.table({column: pa.array(values[column], type=arrow_type(column)) for column in COLUMNS})
    pq.write_table(table, output, compression="snappy")
    return table.num_rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate a synthetic CUR 2.0 file with unblended costs.")
    parser.add_argument("--rows", type=int, default=10000, help="Number of hourly usage lines (default 10000).")
    parser.add_argument("--month", default="2026-10", help="Billing month as YYYY-MM (default 2026-10).")
    parser.add_argument("--seed", type=int, default=7, help="Random seed, so the same options give the same file.")
    parser.add_argument(
        "--output",
        default="samples/cur2_unblended_bigdata_bedrock.csv",
        help="Where to write the file. A name ending in .parquet writes Parquet, which needs pyarrow. "
        "Any other name writes CSV.",
    )
    args = parser.parse_args(argv)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = Generator(args.month, args.seed).rows(args.rows)
    if output.suffix.lower() == ".parquet":
        written = write_parquet(rows, output)
    else:
        written = write_csv(rows, output)
    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"Wrote {written:,} lines and {len(COLUMNS)} columns ({size_mb:.1f} MB) to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
