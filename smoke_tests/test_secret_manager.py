from common import optional_env, print_ok, require_env, require_package

require_package("google.cloud.secretmanager", "pip install -r requirements-google.txt")

from google.cloud import secretmanager


project = require_env("GOOGLE_CLOUD_PROJECT")
client = secretmanager.SecretManagerServiceClient()
parent = f"projects/{project}"
secrets = list(client.list_secrets(request={"parent": parent, "page_size": 5}))
print_ok(f"Secret Manager connected. Secrets visible in first page: {len(secrets)}")

