from common import print_ok, require_env, require_package

require_package("requests", "pip install -r requirements.txt")

import requests


api_key = require_env("SARVAM_API_KEY")
response = requests.post(
    "https://api.sarvam.ai/translate",
    headers={
        "api-subscription-key": api_key,
        "Content-Type": "application/json",
    },
    json={
        "input": "Do not irrigate today.",
        "source_language_code": "en-IN",
        "target_language_code": "hi-IN",
        "model": "mayura:v1",
    },
    timeout=30,
)
response.raise_for_status()
data = response.json()
print(data["translated_text"])
print_ok("Sarvam Translation API responded")
