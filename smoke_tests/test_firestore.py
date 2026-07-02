from common import optional_env, print_ok, require_package

require_package("google.cloud.firestore", "pip install -r requirements-google.txt")

from google.cloud import firestore


project = optional_env("GOOGLE_CLOUD_PROJECT")
client = firestore.Client(project=project)
collections = list(client.collections())
print_ok(f"Firestore connected. Collection count visible to credentials: {len(collections)}")

