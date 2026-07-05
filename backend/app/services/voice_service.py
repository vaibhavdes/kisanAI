import base64
from binascii import Error as BinasciiError

import requests

from app.core.config import settings
from app.models.schemas import (
    FarmerResponse,
    ProviderFeature,
    ProviderName,
    VoiceIntakeRequest,
    VoiceIntakeResponse,
    VoiceSpeakRequest,
    VoiceSpeakResponse,
    VoiceTranscribeRequest,
    VoiceTranscribeResponse,
)
from app.repositories.store import store
from app.services.channel_intent import detect_farmer_intent
from app.utils.language import phrase


class VoiceProviderUnavailable(RuntimeError):
    pass


class VoiceService:
    def handle_intake(self, farmer: FarmerResponse, payload: VoiceIntakeRequest) -> VoiceIntakeResponse:
        language = payload.language or farmer.language
        stt_provider = None
        if payload.transcript:
            transcript = payload.transcript
        else:
            transcription = self.transcribe(
                VoiceTranscribeRequest(
                    farmer_id=farmer.id,
                    audio_base64=payload.audio_base64,
                    audio_uri=payload.audio_uri,
                    language=language,
                    content_type=payload.audio_mime_type,
                )
            )
            transcript = transcription.transcript
            language = transcription.language or language
            stt_provider = transcription.provider

        intent = self._detect_intent(transcript)
        response = self._response_for_intent(intent, self._display_name(farmer.name, language), language)
        tts_provider = None
        audio_base64 = None
        audio_content_type = None
        try:
            speech = self.speak(VoiceSpeakRequest(farmer_id=farmer.id, text=response, language=language))
            tts_provider = speech.provider
            audio_base64 = speech.audio_base64
            audio_content_type = speech.content_type
        except VoiceProviderUnavailable:
            pass
        return VoiceIntakeResponse(
            transcript=transcript,
            detected_intent=intent,
            response_text=response,
            response_language=language,
            audio_url=None,
            stt_provider=stt_provider,
            tts_provider=tts_provider,
            response_audio_base64=audio_base64,
            response_audio_content_type=audio_content_type,
        )

    def transcribe(self, payload: VoiceTranscribeRequest) -> VoiceTranscribeResponse:
        audio = self._load_audio(payload.audio_base64, payload.audio_uri)
        errors: list[str] = []
        for provider in self._provider_order(ProviderFeature.stt):
            try:
                if provider == ProviderName.google_stt:
                    return self._transcribe_with_google(payload, audio)
                if provider == ProviderName.sarvam_stt:
                    return self._transcribe_with_sarvam(payload, audio)
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
        raise VoiceProviderUnavailable("; ".join(errors) or "No STT provider is configured.")

    def speak(self, payload: VoiceSpeakRequest) -> VoiceSpeakResponse:
        errors: list[str] = []
        for provider in self._provider_order(ProviderFeature.tts):
            try:
                if provider == ProviderName.google_tts:
                    return self._speak_with_google(payload)
                if provider == ProviderName.sarvam_tts:
                    return self._speak_with_sarvam(payload)
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
        raise VoiceProviderUnavailable("; ".join(errors) or "No TTS provider is configured.")

    def _detect_intent(self, transcript: str) -> str:
        return detect_farmer_intent(transcript)

    def _response_for_intent(self, intent: str, name: str, language: str) -> str:
        if intent == "irrigation_advisory":
            return phrase("irrigation_response", language, name=name)
        if intent == "crop_diagnosis":
            return phrase("diagnosis_response", language, name=name)
        if intent == "crop_recommendation":
            return phrase("crop_response", language, name=name)
        if intent == "identity_query":
            return phrase("identity_response", language, name=name)
        if intent == "weather_query":
            return phrase("weather_response", language)
        return phrase("general_response", language, name=name, language=language)

    def _display_name(self, name: str, language: str) -> str:
        if name.strip().lower() == "farmer":
            return phrase("farmer_default_name", language)
        return name

    def _transcribe_with_google(
        self,
        payload: VoiceTranscribeRequest,
        audio: bytes,
    ) -> VoiceTranscribeResponse:
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        if not settings.google_cloud_project:
            raise VoiceProviderUnavailable("GOOGLE_CLOUD_PROJECT is required for Google STT.")

        language = payload.language or settings.default_language
        recognizer = (
            f"projects/{settings.google_cloud_project}/locations/"
            f"{settings.google_cloud_location}/recognizers/_"
        )
        client = SpeechClient()
        config = cloud_speech.RecognitionConfig(
            language_codes=[language],
            model="latest_short",
        )
        if payload.audio_encoding.upper() == "LINEAR16":
            config.explicit_decoding_config = cloud_speech.ExplicitDecodingConfig(
                encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=payload.sample_rate_hertz,
                audio_channel_count=1,
            )
        else:
            config.auto_decoding_config = cloud_speech.AutoDetectDecodingConfig()
        request = cloud_speech.RecognizeRequest(
            recognizer=recognizer,
            config=config,
            content=audio,
        )
        response = client.recognize(request=request)
        transcripts = [
            result.alternatives[0].transcript
            for result in response.results
            if result.alternatives and result.alternatives[0].transcript
        ]
        confidence = self._average(
            [
                result.alternatives[0].confidence
                for result in response.results
                if result.alternatives and result.alternatives[0].confidence
            ]
        )
        return VoiceTranscribeResponse(
            transcript=" ".join(transcripts).strip(),
            language=language,
            provider=ProviderName.google_stt.value,
            confidence=confidence,
        )

    def _transcribe_with_sarvam(
        self,
        payload: VoiceTranscribeRequest,
        audio: bytes,
    ) -> VoiceTranscribeResponse:
        if not settings.sarvam_api_key:
            raise VoiceProviderUnavailable("SARVAM_API_KEY is required for Sarvam STT.")

        response = requests.post(
            f"{settings.sarvam_api_base_url.rstrip('/')}/speech-to-text",
            headers={"api-subscription-key": settings.sarvam_api_key},
            files={"file": ("audio.wav", audio, payload.content_type)},
            data={
                "model": settings.sarvam_stt_model,
                "mode": "transcribe",
                "language_code": payload.language or "unknown",
                **self._sarvam_audio_codec(payload.audio_encoding),
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return VoiceTranscribeResponse(
            transcript=str(data.get("transcript") or "").strip(),
            language=data.get("language_code") or payload.language,
            provider=ProviderName.sarvam_stt.value,
            confidence=data.get("language_probability"),
        )

    def _speak_with_google(self, payload: VoiceSpeakRequest) -> VoiceSpeakResponse:
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()
        audio_encoding = self._google_audio_encoding(payload.audio_encoding)
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=payload.text),
            voice=texttospeech.VoiceSelectionParams(language_code=payload.language),
            audio_config=texttospeech.AudioConfig(audio_encoding=audio_encoding),
        )
        return VoiceSpeakResponse(
            audio_base64=base64.b64encode(response.audio_content).decode("ascii"),
            provider=ProviderName.google_tts.value,
            audio_encoding=payload.audio_encoding,
            content_type=self._content_type(payload.audio_encoding),
        )

    def _speak_with_sarvam(self, payload: VoiceSpeakRequest) -> VoiceSpeakResponse:
        if not settings.sarvam_api_key:
            raise VoiceProviderUnavailable("SARVAM_API_KEY is required for Sarvam TTS.")

        response = requests.post(
            f"{settings.sarvam_api_base_url.rstrip('/')}/text-to-speech",
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json={"text": payload.text, "target_language_code": payload.language},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        audios = data.get("audios") or []
        if not audios:
            raise VoiceProviderUnavailable("Sarvam TTS returned no audio.")
        return VoiceSpeakResponse(
            audio_base64=str(audios[0]),
            provider=ProviderName.sarvam_tts.value,
            audio_encoding=payload.audio_encoding,
            content_type=self._content_type(payload.audio_encoding),
        )

    def _provider_order(self, feature: ProviderFeature) -> list[ProviderName]:
        if feature in {ProviderFeature.stt, ProviderFeature.tts} and not (
            settings.enable_google_integrations or settings.sarvam_api_key
        ):
            return []
        route = store.get_provider_route(feature)
        if not route.enabled:
            return []

        providers = [route.primary]
        if route.allow_fallback and route.secondary:
            providers.append(route.secondary)
        if not settings.enable_google_integrations:
            providers = [
                provider
                for provider in providers
                if provider in {ProviderName.sarvam_stt, ProviderName.sarvam_tts}
            ]
        return providers

    def _load_audio(self, audio_base64: str | None, audio_uri: str | None) -> bytes:
        if audio_base64:
            try:
                return base64.b64decode(audio_base64, validate=True)
            except (BinasciiError, ValueError) as exc:
                raise VoiceProviderUnavailable("Invalid audio_base64 payload.") from exc
        if not audio_uri:
            raise VoiceProviderUnavailable("audio_base64 or audio_uri is required for transcription.")
        if audio_uri.startswith("gs://"):
            return self._load_gcs_audio(audio_uri)
        if audio_uri.startswith(("http://", "https://")):
            try:
                response = requests.get(audio_uri, auth=self._twilio_media_auth(audio_uri), timeout=30)
                response.raise_for_status()
                return response.content
            except requests.RequestException as exc:
                raise VoiceProviderUnavailable(f"Audio media download failed: {exc}") from exc
        raise VoiceProviderUnavailable("Only base64, gs://, http://, and https:// audio inputs are supported.")

    def _twilio_media_auth(self, uri: str) -> tuple[str, str] | None:
        if "api.twilio.com" not in uri:
            return None
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            return None
        return settings.twilio_account_sid, settings.twilio_auth_token

    def _load_gcs_audio(self, audio_uri: str) -> bytes:
        from google.cloud import storage

        bucket_name, blob_name = audio_uri.removeprefix("gs://").split("/", 1)
        bucket = storage.Client(project=settings.google_cloud_project).bucket(bucket_name)
        return bucket.blob(blob_name).download_as_bytes()

    def _google_audio_encoding(self, value: str):
        from google.cloud import texttospeech

        normalized = value.upper()
        if normalized == "LINEAR16":
            return texttospeech.AudioEncoding.LINEAR16
        if normalized == "OGG_OPUS":
            return texttospeech.AudioEncoding.OGG_OPUS
        return texttospeech.AudioEncoding.MP3

    def _sarvam_audio_codec(self, audio_encoding: str) -> dict[str, str]:
        if audio_encoding.upper() == "LINEAR16":
            return {"input_audio_codec": "pcm_s16le"}
        return {}

    def _content_type(self, audio_encoding: str) -> str:
        normalized = audio_encoding.upper()
        if normalized == "LINEAR16":
            return "audio/wav"
        if normalized == "OGG_OPUS":
            return "audio/ogg"
        return "audio/mpeg"

    def _average(self, values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None
