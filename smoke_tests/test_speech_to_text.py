from common import optional_env, print_ok, require_package

require_package("google.cloud.speech", "pip install -r requirements-google.txt")

from google.cloud import speech


client_options = {}
project = optional_env("GOOGLE_CLOUD_PROJECT")
client = speech.SpeechClient(**client_options)
print_ok(f"Speech-to-Text client initialized for project hint: {project or 'ADC default'}")

