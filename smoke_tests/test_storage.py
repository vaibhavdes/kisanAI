from common import optional_env, print_ok, require_env, require_package

require_package("google.cloud.storage", "pip install -r requirements.txt")

from google.cloud import storage


project = optional_env("GOOGLE_CLOUD_PROJECT")
bucket_name = require_env("STORAGE_BUCKET")
client = storage.Client(project=project)
bucket = client.bucket(bucket_name)
exists = bucket.exists()
if not exists:
    raise RuntimeError(f"Bucket {bucket_name} not found or credentials cannot access it.")
print_ok(f"Cloud Storage bucket exists: {bucket_name}")
