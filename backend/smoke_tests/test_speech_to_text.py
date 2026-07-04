from common import optional_env, print_ok, require_env, require_package

require_package("google.cloud.speech_v2", "pip install -r requirements.txt")

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


project = require_env("GOOGLE_CLOUD_PROJECT")
location = optional_env("GOOGLE_CLOUD_LOCATION", "global")
language = optional_env("STT_TEST_LANGUAGE", "en-IN")

client = SpeechClient()
recognizer = f"projects/{project}/locations/{location}/recognizers/_"
audio = b"\0" * 32000
config = cloud_speech.RecognitionConfig(
    explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
        encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        audio_channel_count=1,
    ),
    language_codes=[language],
    model="latest_short",
)
request = cloud_speech.RecognizeRequest(
    recognizer=recognizer,
    config=config,
    content=audio,
)
response = client.recognize(request=request)
print_ok(
    f"Speech-to-Text v2 responded for {recognizer}; "
    f"language={language}; results={len(response.results)}"
)
