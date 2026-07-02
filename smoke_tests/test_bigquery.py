from common import optional_env, print_ok, require_package

require_package("google.cloud.bigquery", "pip install -r requirements-google.txt")

from google.cloud import bigquery


project = optional_env("GOOGLE_CLOUD_PROJECT")
client = bigquery.Client(project=project)
datasets = list(client.list_datasets(max_results=10))
print_ok(f"BigQuery connected. Dataset count visible in first page: {len(datasets)}")

