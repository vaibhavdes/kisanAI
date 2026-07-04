from common import optional_env, print_ok, require_package

require_package("google.cloud.firestore", "pip install -r requirements.txt")

from google.cloud import firestore


project = optional_env("GOOGLE_CLOUD_PROJECT")
database = optional_env("FIRESTORE_DATABASE", "(default)")
client = firestore.Client(project=project, database=database)
collections = list(client.collections())
print_ok(f"Firestore database {database} connected. Collection count visible to credentials: {len(collections)}")
