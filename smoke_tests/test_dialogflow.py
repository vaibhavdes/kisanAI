from common import optional_env, print_ok, require_env, require_package

require_package("google.cloud.dialogflowcx_v3", "pip install -r requirements-google.txt")

from google.cloud.dialogflowcx_v3 import AgentsClient


project = require_env("GOOGLE_CLOUD_PROJECT")
location = optional_env("DIALOGFLOW_LOCATION", "global")
client = AgentsClient()
parent = f"projects/{project}/locations/{location}"
agents = list(client.list_agents(request={"parent": parent, "page_size": 5}))
print_ok(f"Dialogflow CX connected. Agents visible in first page: {len(agents)}")

