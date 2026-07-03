from common import optional_env, print_ok, require_env, require_package

require_package("google.genai", "pip install -r requirements.txt")

from google import genai


project = require_env("GOOGLE_CLOUD_PROJECT")
location = optional_env("GOOGLE_CLOUD_LOCATION", "global")
model = optional_env("VERTEX_AI_MODEL", "gemini-2.5-flash")

client = genai.Client(vertexai=True, project=project, location=location)

prompt = """
You are KISAN-AI, an agricultural advisory assistant.

Give a short Hindi advisory for a cotton farmer before heavy rain.
Mention one action to take and one action to avoid.
"""

response = client.models.generate_content(model=model, contents=prompt)
print(response.text)
print_ok(f"Vertex AI responded using {model} in {location}")
