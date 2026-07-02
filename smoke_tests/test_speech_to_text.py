from common import optional_env, print_ok, require_package

require_package("google.cloud.speech", "pip install -r requirements.txt")

from google.cloud import speech


client_options = {}
project = optional_env("GOOGLE_CLOUD_PROJECT")
client = speech.SpeechClient(**client_options)
audio = speech.RecognitionAudio(content=b"\0" * 32000)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="en-US",
)
response = client.recognize(config=config, audio=audio)
print_ok(
    "Speech-to-Text API responded "
    f"for project hint: {project or 'ADC default'}; results={len(response.results)}"
)
