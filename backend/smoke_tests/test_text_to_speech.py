from common import print_ok, require_package

require_package("google.cloud.texttospeech", "pip install -r requirements.txt")

from google.cloud import texttospeech


client = texttospeech.TextToSpeechClient()
input_text = texttospeech.SynthesisInput(text="पुढील दोन दिवस फवारणी करू नका.")
voice = texttospeech.VoiceSelectionParams(language_code="mr-IN")
audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
print_ok(f"Text-to-Speech generated {len(response.audio_content)} bytes")
