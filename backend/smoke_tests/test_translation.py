from common import print_ok, require_package

require_package("google.cloud.translate_v3", "pip install -r requirements.txt")

from google.cloud import translate_v3 as translate

from common import optional_env, require_env


project = require_env("GOOGLE_CLOUD_PROJECT")
location = optional_env("GOOGLE_CLOUD_LOCATION", "global")
client = translate.TranslationServiceClient()
parent = f"projects/{project}/locations/{location}"
response = client.translate_text(
    request={
        "parent": parent,
        "contents": ["नमस्कार शेतकरी मित्र"],
        "mime_type": "text/plain",
        "source_language_code": "mr",
        "target_language_code": "en",
    }
)
print(response.translations[0].translated_text)
print_ok("Translation API responded")
