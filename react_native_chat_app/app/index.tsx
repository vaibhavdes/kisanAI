import {
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioPlayer,
  useAudioRecorder,
  useAudioRecorderState,
} from "expo-audio";
import * as FileSystem from "expo-file-system/legacy";
import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  KeyboardAvoidingView,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { apiBaseUrl, saveSensorReading, sendChatMessage } from "@/api/client";
import { languages } from "@/constants/languages";
import { autoLanguageCode, copyLanguage, languageForState, uiCopy } from "@/i18n/ui";
import type { ChatMessage, ChatPayload, ChatResponse } from "@/types/chat";

const whatsAppGreen = "#075e54";
const whatsAppLightGreen = "#128c7e";
const bubbleMine = "#dcf8c6";
const bubbleTheirs = "#ffffff";
const wallpaper = "#efe7da";
const border = "#d9d4c8";
const twilioWhatsAppNumber = "+1 415 523 8886";
const twilioWhatsAppJoinCode = "join first-dig";
const twilioWhatsAppUrl = `https://wa.me/14155238886?text=${encodeURIComponent(twilioWhatsAppJoinCode)}`;

export default function IndexScreen() {
  const [phone, setPhone] = useState("");
  const [language, setLanguage] = useState(autoLanguageCode);
  const [languageTouched, setLanguageTouched] = useState(false);
  const [suggestedLanguage, setSuggestedLanguage] = useState<string | undefined>();
  const [started, setStarted] = useState(false);
  const copy = uiCopy(copyLanguage(language === autoLanguageCode && suggestedLanguage ? suggestedLanguage : language));

  useEffect(() => {
    let active = true;
    async function detectLastKnownState() {
      try {
        const permission = await Location.getForegroundPermissionsAsync();
        if (!permission.granted) return;
        const position = await Location.getLastKnownPositionAsync({});
        if (!position) return;
        const [address] = await Location.reverseGeocodeAsync(position.coords);
        const detected = languageForState(address?.region);
        if (active && detected) {
          setSuggestedLanguage(detected);
          if (!languageTouched && language === autoLanguageCode) {
            setLanguage(detected);
          }
        }
      } catch {
        // Location-based language is only a convenience. Chat still works without it.
      }
    }
    detectLastKnownState();
    return () => {
      active = false;
    };
  }, [language, languageTouched]);

  function changeLanguage(value: string) {
    setLanguageTouched(true);
    setLanguage(value);
  }

  if (!started) {
    return (
      <OnboardingScreen
        phone={phone}
        language={language}
        suggestedLanguage={suggestedLanguage}
        copy={copy}
        onPhoneChange={setPhone}
        onLanguageChange={changeLanguage}
        onStart={() => {
          if (!phone.trim()) {
            Alert.alert(copy.phoneRequiredTitle, copy.phoneRequiredMessage);
            return;
          }
          setStarted(true);
        }}
      />
    );
  }

  return (
    <ChatScreen
      phone={phone.trim()}
      language={language}
      suggestedLanguage={suggestedLanguage}
      copy={copy}
      onLanguageChange={changeLanguage}
      onStateLanguageDetected={(value) => {
        setSuggestedLanguage(value);
        if (!languageTouched && language === autoLanguageCode) {
          setLanguage(value);
        }
      }}
    />
  );
}

function OnboardingScreen({
  phone,
  language,
  suggestedLanguage,
  copy,
  onPhoneChange,
  onLanguageChange,
  onStart,
}: {
  phone: string;
  language: string;
  suggestedLanguage?: string;
  copy: ReturnType<typeof uiCopy>;
  onPhoneChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onStart: () => void;
}) {
  const insets = useSafeAreaInsets();
  const languageOptions = [{ code: autoLanguageCode, label: "Auto" }, ...languages];

  async function openWhatsAppSandbox() {
    try {
      await Linking.openURL(twilioWhatsAppUrl);
    } catch {
      Alert.alert(copy.whatsAppOpenFailedTitle, copy.whatsAppOpenFailedMessage);
    }
  }

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      style={{ flex: 1, backgroundColor: wallpaper }}
      contentContainerStyle={{
        minHeight: "100%",
        paddingTop: insets.top + 30,
        paddingBottom: insets.bottom + 24,
        paddingHorizontal: 22,
        gap: 22,
      }}
    >
      <View style={{ gap: 10 }}>
        <View
          style={{
            width: 70,
            height: 70,
            borderRadius: 35,
            backgroundColor: whatsAppGreen,
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 12px rgba(0,0,0,0.18)",
          }}
        >
          <Text selectable={false} style={{ color: "#fff", fontSize: 25, fontWeight: "900" }}>
            AI
          </Text>
        </View>
        <Text selectable style={{ fontSize: 34, fontWeight: "900", color: "#172017" }}>
          {copy.appName}
        </Text>
        <Text selectable style={{ color: "#526052", fontSize: 16, lineHeight: 23 }}>
          {copy.appTagline}
        </Text>
      </View>

      <View style={{ gap: 10 }}>
        <Text selectable style={{ fontWeight: "800", color: "#263426" }}>
          {copy.farmerPhone}
        </Text>
        <TextInput
          value={phone}
          onChangeText={onPhoneChange}
          keyboardType="phone-pad"
          placeholder="+91 9970983794"
          placeholderTextColor="#8b958b"
          style={{
            minHeight: 54,
            borderWidth: 1,
            borderColor: border,
            borderRadius: 14,
            paddingHorizontal: 14,
            backgroundColor: "#fff",
            fontSize: 17,
          }}
        />
      </View>

      <View style={{ gap: 10 }}>
        <Text selectable style={{ fontWeight: "800", color: "#263426" }}>
          {copy.replyLanguage}
        </Text>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 9 }}>
          {languageOptions.map((item) => {
            const selected = language === item.code;
            const suggested = suggestedLanguage === item.code;
            return (
              <Pressable
                key={item.code}
                onPress={() => onLanguageChange(item.code)}
                style={{
                  paddingHorizontal: 14,
                  paddingVertical: 10,
                  borderRadius: 999,
                  borderWidth: 1,
                  borderColor: selected ? whatsAppLightGreen : suggested ? "#d4a62d" : border,
                  backgroundColor: selected ? "#dff4eb" : "#fff",
                }}
              >
                <Text selectable={false} style={{ color: selected ? whatsAppGreen : "#263426", fontWeight: "800" }}>
                  {item.code === autoLanguageCode ? copy.autoLanguage : item.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <Text selectable style={{ color: "#667266", fontSize: 12, lineHeight: 17 }}>
          {copy.autoLanguageHint}
          {suggestedLanguage ? ` ${copy.suggestedLanguage}: ${languageLabel(suggestedLanguage)}.` : ""}
        </Text>
      </View>

      <View style={{ flex: 1 }} />
      <Pressable
        onPress={openWhatsAppSandbox}
        style={{
          minHeight: 58,
          borderRadius: 18,
          borderWidth: 1,
          borderColor: "#b9dfcf",
          backgroundColor: "#ecfff6",
          paddingHorizontal: 14,
          paddingVertical: 11,
          flexDirection: "row",
          alignItems: "center",
          gap: 12,
        }}
      >
        <View
          style={{
            width: 38,
            height: 38,
            borderRadius: 19,
            backgroundColor: "#25d366",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text selectable={false} style={{ color: "#fff", fontSize: 11, fontWeight: "900" }}>
            WA
          </Text>
        </View>
        <View style={{ flex: 1, gap: 2 }}>
          <Text selectable={false} style={{ color: whatsAppGreen, fontSize: 16, fontWeight: "900" }}>
            {copy.chatOnWhatsApp}
          </Text>
          <Text selectable style={{ color: "#405a4d", fontSize: 12, lineHeight: 17 }}>
            {copy.whatsAppSandboxHint.replace("+1 415 523 8886", twilioWhatsAppNumber)}
          </Text>
          <Text selectable style={{ color: "#0f4d3d", fontSize: 12, fontWeight: "900", lineHeight: 17 }}>
            {copy.whatsAppSandboxCode}
          </Text>
        </View>
      </Pressable>
      <Pressable
        onPress={onStart}
        style={{
          minHeight: 54,
          borderRadius: 999,
          backgroundColor: whatsAppGreen,
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 4px 12px rgba(7,94,84,0.28)",
        }}
      >
        <Text selectable={false} style={{ color: "#fff", fontWeight: "900", fontSize: 16 }}>
          {copy.startChat}
        </Text>
      </Pressable>
    </ScrollView>
  );
}

function ChatScreen({
  phone,
  language,
  suggestedLanguage,
  copy,
  onLanguageChange,
  onStateLanguageDetected,
}: {
  phone: string;
  language: string;
  suggestedLanguage?: string;
  copy: ReturnType<typeof uiCopy>;
  onLanguageChange: (value: string) => void;
  onStateLanguageDetected: (language: string) => void;
}) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const scrollRef = useRef<ScrollView>(null);
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recorderState = useAudioRecorderState(audioRecorder);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [attachmentsOpen, setAttachmentsOpen] = useState(false);
  const [sensorOpen, setSensorOpen] = useState(false);
  const [farmerId, setFarmerId] = useState<string | undefined>();
  const [soilMoisture, setSoilMoisture] = useState("0.16");
  const [soilTemp, setSoilTemp] = useState("29.4");
  const [airTemp, setAirTemp] = useState("34.1");
  const [humidity, setHumidity] = useState("62");
  const [rainfall, setRainfall] = useState("0");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      text: copy.welcome,
      mine: false,
      kind: "system",
      time: currentTime(),
    },
  ]);

  useEffect(() => {
    setMessages((current) =>
      current.map((message) => (message.id === "welcome" ? { ...message, text: copy.welcome } : message)),
    );
  }, [copy.welcome]);

  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [messages.length]);

  function payloadLanguage() {
    return language === autoLanguageCode ? undefined : language;
  }

  async function sendPayload(userMessage: ChatMessage, payload: ChatPayload) {
    const localId = userMessage.id;
    const processingId = `${Date.now()}-processing`;
    setMessages((current) => [...current, { ...userMessage, status: "sending", time: currentTime() }]);
    setMessages((current) => [
      ...current,
      {
        id: processingId,
        text: "Checking farm data...",
        mine: false,
        kind: "system",
        intent: "processing",
        time: currentTime(),
      },
    ]);
    setSending(true);
    try {
      const response = await sendChatMessage({ ...payload, language: payloadLanguage() });
      if (response.farmer_id) setFarmerId(response.farmer_id);
      setMessages((current) =>
        current
          .filter((message) => message.id !== processingId)
          .map((message) => (message.id === localId ? { ...message, status: "sent" } : message)),
      );
      setMessages((current) => [...current, responseToMessage(response, copy)]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Backend request failed.";
      setMessages((current) =>
        current
          .filter((item) => item.id !== processingId)
          .map((item) => (item.id === localId ? { ...item, status: "failed" } : item)),
      );
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-error`,
          text: `${copy.backendFailed} at ${apiBaseUrl}. ${message}`,
          mine: false,
          kind: "system",
          intent: "error",
          time: currentTime(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  function sendText() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    sendPayload(
      {
        id: `${Date.now()}-user`,
        text,
        mine: true,
        kind: "text",
      },
      {
        from_phone: phone,
        text,
      },
    );
  }

  async function shareLocation() {
    if (sending) return;
    setAttachmentsOpen(false);
    const permission = await Location.requestForegroundPermissionsAsync();
    if (!permission.granted) {
      Alert.alert(copy.locationPermissionTitle, copy.locationPermissionMessage);
      return;
    }
    const position = await Location.getCurrentPositionAsync({});
    try {
      const [address] = await Location.reverseGeocodeAsync(position.coords);
      const detected = languageForState(address?.region);
      if (detected) onStateLanguageDetected(detected);
    } catch {
      // Reverse geocoding is optional for the chat request.
    }
    const coords = `${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`;
    await sendPayload(
      {
        id: `${Date.now()}-location`,
        text: `${copy.locationShared}\n${coords}`,
        mine: true,
        kind: "location",
      },
      {
        from_phone: phone,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        location_label: copy.locationLabel,
      },
    );
  }

  async function attachPhoto(useCamera: boolean) {
    if (sending) return;
    setAttachmentsOpen(false);
    const permission = useCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert(copy.photoPermissionTitle, copy.photoPermissionMessage);
      return;
    }

    const result = useCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.72, base64: true })
      : await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          quality: 0.72,
          base64: true,
        });

    if (result.canceled || !result.assets[0]) return;
    const asset = result.assets[0];
    if (!asset.base64) {
      Alert.alert(copy.photoUploadFailedTitle, copy.photoUploadFailedMessage);
      return;
    }
    const caption = input.trim() || copy.cropPhotoCaption;
    setInput("");
    await sendPayload(
      {
        id: `${Date.now()}-image`,
        text: caption,
        mine: true,
        kind: "image",
        mediaUri: asset.uri,
      },
      {
        from_phone: phone,
        text: caption,
        media_type: "image",
        media_base64: asset.base64,
        media_mime_type: asset.mimeType || "image/jpeg",
      },
    );
  }

  async function toggleRecording() {
    if (sending) return;
    if (recorderState.isRecording) {
      await stopRecording();
      return;
    }
    const permission = await AudioModule.requestRecordingPermissionsAsync();
    if (!permission.granted) {
      Alert.alert(copy.microphonePermissionTitle, copy.microphonePermissionMessage);
      return;
    }
    await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
    await audioRecorder.prepareToRecordAsync();
    audioRecorder.record();
  }

  async function stopRecording() {
    await audioRecorder.stop();
    const uri = audioRecorder.uri || recorderState.url;
    if (!uri) {
      Alert.alert(copy.voiceFailedTitle, copy.voiceFailedMessage);
      return;
    }
    const typedCaption = input.trim();
    let base64: string;
    try {
      base64 = await uriToBase64(uri);
    } catch {
      Alert.alert(copy.voiceFailedTitle, copy.voiceUploadFailedMessage);
      return;
    }
    setInput("");
    await sendPayload(
      {
        id: `${Date.now()}-audio`,
        text: typedCaption || copy.voiceNote(Math.max(1, Math.round(recorderState.durationMillis / 1000))),
        mine: true,
        kind: "audio",
        audioUri: uri,
      },
      {
        from_phone: phone,
        text: typedCaption || undefined,
        media_type: "audio",
        audio_base64: base64,
        audio_mime_type: audioMimeType(uri),
      },
    );
  }

  async function submitSensorReading() {
    if (!farmerId) {
      Alert.alert("Farmer context needed", "Send one message first so the app can identify the farmer.");
      return;
    }
    setSensorOpen(false);
    try {
      const response = await saveSensorReading({
        farmer_id: farmerId,
        sensor_id: "manual_sensor_01",
        source: "farmer_app_manual_entry",
        device_type: "soil_moisture_sensor",
        timestamp: new Date().toISOString(),
        readings: {
          soil_moisture: numberOrNull(soilMoisture),
          soil_temperature_c: numberOrNull(soilTemp),
          air_temperature_c: numberOrNull(airTemp),
          humidity_percent: numberOrNull(humidity),
          rainfall_mm: numberOrNull(rainfall),
        },
      });
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-sensor`,
          text: `Sensor reading saved. Moisture risk: ${response.reading.soil_moisture_risk}. ${response.advisory_hint}`,
          mine: false,
          kind: "system",
          intent: "sensor_reading",
          time: currentTime(),
        },
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Sensor reading failed.";
      Alert.alert("Sensor reading failed", message);
    }
  }

  async function startLiveCall() {
    const voiceNumber = "+17752698657";
    const canOpen = await Linking.canOpenURL(`tel:${voiceNumber}`);
    if (!canOpen) {
      Alert.alert("Voice call", `Call ${voiceNumber} from your phone to test Kisan Alert voice advisory.`);
      return;
    }
    await Linking.openURL(`tel:${voiceNumber}`);
    setMessages((current) => [
      ...current,
      {
        id: `${Date.now()}-live`,
        text: `Opening phone call to ${voiceNumber}. The Twilio number should be configured to POST voice webhooks to /api/v1/twilio/voice.`,
        mine: false,
        kind: "system",
        intent: "voice_call",
        time: currentTime(),
      },
    ]);
  }

  const maxBubbleWidth = Math.min(width * 0.78, 620);

  return (
    <KeyboardAvoidingView
      behavior={Platform.select({ ios: "padding", default: undefined })}
      style={{ flex: 1, backgroundColor: wallpaper }}
    >
      <View
        style={{
          paddingTop: insets.top + 8,
          paddingHorizontal: 10,
          paddingBottom: 8,
          backgroundColor: whatsAppGreen,
          flexDirection: "row",
          alignItems: "center",
          gap: 10,
        }}
      >
        <View
          style={{
            width: 42,
            height: 42,
            borderRadius: 21,
            backgroundColor: whatsAppLightGreen,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text selectable={false} style={{ color: "#fff", fontSize: 14, fontWeight: "900" }}>
            AI
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text selectable style={{ color: "#fff", fontSize: 17, fontWeight: "900" }} numberOfLines={1}>
            {copy.appName}
          </Text>
          <Text selectable style={{ color: "#d4eee8", fontSize: 12 }} numberOfLines={1}>
            {phone} · {language === autoLanguageCode ? copy.autoLanguageShort : languageLabel(language)}
          </Text>
        </View>
        <LanguageMenu value={language} suggestedLanguage={suggestedLanguage} copy={copy} onChange={onLanguageChange} />
      </View>

      <ScrollView
        ref={scrollRef}
        contentInsetAdjustmentBehavior="automatic"
        keyboardShouldPersistTaps="handled"
        style={{ flex: 1 }}
        contentContainerStyle={{ padding: 10, gap: 6 }}
      >
        <View
          style={{
            alignSelf: "center",
            backgroundColor: "rgba(255,255,255,0.78)",
            paddingHorizontal: 10,
            paddingVertical: 5,
            borderRadius: 8,
            marginBottom: 4,
          }}
        >
          <Text selectable style={{ color: "#627062", fontSize: 11 }}>
            Backend {apiBaseUrl}
          </Text>
        </View>
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} maxWidth={maxBubbleWidth} copy={copy} />
        ))}
      </ScrollView>

      {sending ? <ActivityIndicator style={{ paddingVertical: 5 }} color={whatsAppGreen} /> : null}

      {attachmentsOpen ? (
        <View
          style={{
            marginHorizontal: 8,
            marginBottom: 6,
            borderRadius: 18,
            backgroundColor: "#fff",
            padding: 12,
            flexDirection: "row",
            gap: 10,
            boxShadow: "0 4px 14px rgba(0,0,0,0.13)",
          }}
        >
          <AttachmentAction label={copy.camera} icon="📷" onPress={() => attachPhoto(true)} />
          <AttachmentAction label={copy.gallery} icon="🖼" onPress={() => attachPhoto(false)} />
          <AttachmentAction label={copy.location} icon="📍" onPress={shareLocation} />
          <AttachmentAction label="Sensor" icon="🌡" onPress={() => setSensorOpen(true)} />
          <AttachmentAction label="Live" icon="☎" onPress={startLiveCall} />
        </View>
      ) : null}

      <Modal visible={sensorOpen} transparent animationType="fade" onRequestClose={() => setSensorOpen(false)}>
        <View style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.28)", justifyContent: "center", padding: 18 }}>
          <View style={{ backgroundColor: "#fff", borderRadius: 18, padding: 16, gap: 12 }}>
            <Text selectable style={{ fontSize: 18, fontWeight: "900", color: "#172017" }}>
              Sensor reading
            </Text>
            <View style={{ flexDirection: "row", gap: 8 }}>
              <SensorInput label="Soil moisture" value={soilMoisture} onChangeText={setSoilMoisture} />
              <SensorInput label="Rain mm" value={rainfall} onChangeText={setRainfall} />
            </View>
            <View style={{ flexDirection: "row", gap: 8 }}>
              <SensorInput label="Soil C" value={soilTemp} onChangeText={setSoilTemp} />
              <SensorInput label="Air C" value={airTemp} onChangeText={setAirTemp} />
              <SensorInput label="Humidity %" value={humidity} onChangeText={setHumidity} />
            </View>
            <View style={{ flexDirection: "row", gap: 10, justifyContent: "flex-end" }}>
              <Pressable onPress={() => setSensorOpen(false)} style={{ paddingHorizontal: 14, paddingVertical: 10 }}>
                <Text selectable={false} style={{ color: "#526052", fontWeight: "900" }}>Cancel</Text>
              </Pressable>
              <Pressable
                onPress={submitSensorReading}
                style={{ backgroundColor: whatsAppGreen, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 10 }}
              >
                <Text selectable={false} style={{ color: "#fff", fontWeight: "900" }}>Save</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      <View
        style={{
          paddingBottom: insets.bottom + 7,
          paddingTop: 7,
          paddingHorizontal: 7,
          backgroundColor: "transparent",
          flexDirection: "row",
          alignItems: "flex-end",
          gap: 7,
        }}
      >
        <View
          style={{
            flex: 1,
            minHeight: 48,
            maxHeight: 126,
            borderRadius: 24,
            backgroundColor: "#fff",
            borderWidth: 1,
            borderColor: "#e5e0d6",
            flexDirection: "row",
            alignItems: "flex-end",
            paddingLeft: 6,
            paddingRight: 10,
            paddingVertical: 5,
            gap: 5,
          }}
        >
          <Pressable
            onPress={() => setAttachmentsOpen((open) => !open)}
            disabled={sending}
            style={{
              width: 38,
              height: 38,
              borderRadius: 19,
              alignItems: "center",
              justifyContent: "center",
              opacity: sending ? 0.5 : 1,
            }}
          >
            <Text selectable={false} style={{ color: whatsAppGreen, fontSize: 28, lineHeight: 30 }}>
              +
            </Text>
          </Pressable>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder={recorderState.isRecording ? copy.recordingPlaceholder : copy.messagePlaceholder}
            placeholderTextColor="#7a837a"
            multiline
            style={{
              flex: 1,
              minHeight: 38,
              maxHeight: 112,
              paddingTop: 9,
              paddingBottom: 8,
              fontSize: 16,
              color: "#151d15",
            }}
          />
          <Pressable
            onPress={() => attachPhoto(true)}
            disabled={sending}
            style={{
              width: 36,
              height: 38,
              alignItems: "center",
              justifyContent: "center",
              opacity: sending ? 0.5 : 1,
            }}
          >
            <Text selectable={false} style={{ color: "#627062", fontSize: 21 }}>
              📷
            </Text>
          </Pressable>
        </View>

        <Pressable
          onPress={input.trim() ? sendText : toggleRecording}
          disabled={sending}
          style={{
            width: 48,
            height: 48,
            borderRadius: 24,
            backgroundColor: recorderState.isRecording ? "#b00020" : whatsAppGreen,
            alignItems: "center",
            justifyContent: "center",
            opacity: sending ? 0.55 : 1,
            boxShadow: "0 3px 10px rgba(0,0,0,0.2)",
          }}
        >
          <Text selectable={false} style={{ color: "#fff", fontSize: input.trim() ? 21 : 22, fontWeight: "900" }}>
            {input.trim() ? "➤" : recorderState.isRecording ? "■" : "🎙"}
          </Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

function LanguageMenu({
  value,
  suggestedLanguage,
  copy,
  onChange,
}: {
  value: string;
  suggestedLanguage?: string;
  copy: ReturnType<typeof uiCopy>;
  onChange: (value: string) => void;
}) {
  const languageOptions = [{ code: autoLanguageCode, label: "Auto" }, ...languages];
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxWidth: 104 }}>
      <View style={{ flexDirection: "row", gap: 6 }}>
        {languageOptions.map((item) => {
          const selected = item.code === value;
          const suggested = item.code === suggestedLanguage;
          return (
            <Pressable
              key={item.code}
              onPress={() => onChange(item.code)}
              style={{
                paddingHorizontal: 9,
                paddingVertical: 7,
                borderRadius: 999,
                backgroundColor: selected ? "#e7fff1" : suggested ? "rgba(255,226,130,0.35)" : "rgba(255,255,255,0.16)",
              }}
            >
              <Text selectable={false} style={{ color: selected ? whatsAppGreen : "#fff", fontWeight: "800" }}>
                {item.code === autoLanguageCode ? copy.autoLanguage : item.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </ScrollView>
  );
}

function AttachmentAction({ label, icon, onPress }: { label: string; icon: string; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={{
        flex: 1,
        alignItems: "center",
        gap: 7,
        paddingVertical: 8,
      }}
    >
      <View
        style={{
          width: 48,
          height: 48,
          borderRadius: 24,
          backgroundColor: "#e9f5ef",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Text selectable={false} style={{ fontSize: 22 }}>
          {icon}
        </Text>
      </View>
      <Text selectable={false} style={{ color: "#394639", fontWeight: "800", fontSize: 12 }}>
        {label}
      </Text>
    </Pressable>
  );
}

function SensorInput({
  label,
  value,
  onChangeText,
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
}) {
  return (
    <View style={{ flex: 1, gap: 5 }}>
      <Text selectable style={{ color: "#526052", fontSize: 12, fontWeight: "800" }}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        keyboardType="decimal-pad"
        style={{
          minHeight: 42,
          borderRadius: 12,
          borderWidth: 1,
          borderColor: border,
          paddingHorizontal: 10,
          color: "#172017",
        }}
      />
    </View>
  );
}

function MessageBubble({
  message,
  maxWidth,
  copy,
}: {
  message: ChatMessage;
  maxWidth: number;
  copy: ReturnType<typeof uiCopy>;
}) {
  const audioPlayer = useAudioPlayer(message.audioUri ? { uri: message.audioUri } : null);
  const hasAutoPlayed = useRef(false);
  const isSystem = message.kind === "system";

  useEffect(() => {
    if (!message.mine && message.audioUri && !hasAutoPlayed.current) {
      hasAutoPlayed.current = true;
      audioPlayer.play();
    }
  }, [audioPlayer, message.audioUri, message.mine]);

  return (
    <View style={{ alignItems: isSystem ? "center" : message.mine ? "flex-end" : "flex-start" }}>
      <View
        style={{
          maxWidth: isSystem ? Math.min(maxWidth, 440) : maxWidth,
          paddingHorizontal: isSystem ? 10 : 8,
          paddingVertical: isSystem ? 7 : 6,
          borderRadius: isSystem ? 10 : 9,
          backgroundColor: isSystem ? "rgba(255,255,255,0.8)" : message.mine ? bubbleMine : bubbleTheirs,
          borderTopRightRadius: !isSystem && message.mine ? 2 : 9,
          borderTopLeftRadius: !isSystem && !message.mine ? 2 : 9,
          borderWidth: isSystem ? 0 : 1,
          borderColor: message.mine ? "#c7e9b9" : "#ebe6dc",
          boxShadow: isSystem ? undefined : "0 1px 1px rgba(0,0,0,0.12)",
          gap: 5,
        }}
      >
        {message.mediaUri ? (
          <Image
            source={{ uri: message.mediaUri }}
            style={{
              width: Math.min(maxWidth - 20, 260),
              height: 170,
              borderRadius: 8,
              backgroundColor: "#e7e2d8",
            }}
            resizeMode="cover"
          />
        ) : null}

        {message.kind === "location" ? (
          <View
            style={{
              width: Math.min(maxWidth - 20, 260),
              minHeight: 96,
              borderRadius: 8,
              backgroundColor: "#dfeee6",
              alignItems: "center",
              justifyContent: "center",
              borderWidth: 1,
              borderColor: "#c5ded0",
            }}
          >
            <Text selectable={false} style={{ fontSize: 28 }}>
              📍
            </Text>
            <Text selectable style={{ color: whatsAppGreen, fontWeight: "900", marginTop: 4 }}>
              {copy.farmLocation}
            </Text>
          </View>
        ) : null}

        {message.audioUri ? (
          <Pressable
            onPress={() => audioPlayer.play()}
            style={{
              minWidth: 180,
              minHeight: 42,
              borderRadius: 21,
              backgroundColor: message.mine ? "#c8efba" : "#edf4ef",
              flexDirection: "row",
              alignItems: "center",
              gap: 9,
              paddingHorizontal: 12,
            }}
          >
            <Text selectable={false} style={{ color: whatsAppGreen, fontSize: 16, fontWeight: "900" }}>
              ▶
            </Text>
            <View style={{ flex: 1, height: 3, borderRadius: 2, backgroundColor: "#8eb49b" }} />
            <Text selectable={false} style={{ color: "#536053", fontSize: 12, fontWeight: "800" }}>
              {copy.voice}
            </Text>
          </Pressable>
        ) : null}

        {message.text ? (
          <Text selectable style={{ fontSize: isSystem ? 12 : 15.5, color: "#172017", lineHeight: isSystem ? 17 : 21 }}>
            {message.text}
          </Text>
        ) : null}

        {!message.mine && message.dataSources && Object.keys(message.dataSources).length ? (
          <MetaLine label="Data" value={compactMetadata(message.dataSources)} />
        ) : null}

        {!message.mine && message.serviceWarnings?.length ? (
          <MetaLine label="Issue" value={message.serviceWarnings.join(" · ")} danger />
        ) : null}

        <View style={{ flexDirection: "row", alignSelf: "flex-end", alignItems: "center", gap: 4 }}>
          {message.intent ? (
            <Text selectable style={{ fontSize: 10.5, color: "#687568" }}>
              {message.intent}
            </Text>
          ) : null}
          {message.time ? (
            <Text selectable={false} style={{ fontSize: 10.5, color: "#687568" }}>
              {message.time}
            </Text>
          ) : null}
          {message.mine && message.status ? (
            <Text selectable={false} style={{ fontSize: 11, color: message.status === "failed" ? "#b00020" : "#4f8b6a" }}>
              {message.status === "failed" ? "!" : message.status === "sending" ? "…" : "✓✓"}
            </Text>
          ) : null}
        </View>
      </View>
    </View>
  );
}

function responseToMessage(response: ChatResponse, copy: ReturnType<typeof uiCopy>): ChatMessage {
  const audioUri =
    response.response_audio_base64 && response.response_audio_content_type
      ? `data:${response.response_audio_content_type};base64,${response.response_audio_base64}`
      : undefined;
  return {
    id: `${Date.now()}-assistant`,
    text: response.transcript ? `${response.reply}\n\n${copy.heard}: ${response.transcript}` : response.reply,
    mine: false,
    kind: response.media_url ? "image" : audioUri ? "audio" : "text",
    mediaUri: response.media_url || undefined,
    audioUri,
    audioContentType: response.response_audio_content_type,
    intent: response.intent,
    status: "sent",
    time: currentTime(),
    dataSources: cleanMetadata(response.data_sources),
    serviceWarnings: response.service_warnings || [],
    storedContext: cleanMetadata(response.stored_context),
  };
}

function MetaLine({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return (
    <View
      style={{
        borderTopWidth: 1,
        borderTopColor: danger ? "#f0c8c8" : "#dde8dd",
        paddingTop: 5,
        marginTop: 1,
      }}
    >
      <Text selectable style={{ color: danger ? "#9f1d1d" : "#536053", fontSize: 10.5, lineHeight: 15 }}>
        {label}: {value}
      </Text>
    </View>
  );
}

function cleanMetadata(metadata?: Record<string, string | number | boolean | null | undefined>) {
  if (!metadata) return undefined;
  const entries = Object.entries(metadata).filter(([, value]) => value !== null && value !== undefined && value !== "");
  return entries.length ? Object.fromEntries(entries) : undefined;
}

function compactMetadata(metadata: Record<string, string | number | boolean | null | undefined>) {
  return Object.entries(metadata)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .slice(0, 5)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(" · ");
}

async function uriToBase64(uri: string) {
  if (uri.startsWith("blob:")) {
    const blob = await fetch(uri).then((response) => response.blob());
    const buffer = await blob.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    let binary = "";
    const chunkSize = 0x8000;
    for (let index = 0; index < bytes.length; index += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
    }
    return btoa(binary);
  }
  return FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
}

function audioMimeType(uri: string, fallback = "audio/mp4") {
  const lower = uri.toLowerCase();
  if (lower.startsWith("blob:")) return fallback;
  if (lower.endsWith(".wav")) return "audio/wav";
  if (lower.endsWith(".mp3")) return "audio/mpeg";
  if (lower.endsWith(".ogg") || lower.endsWith(".oga")) return "audio/ogg";
  if (lower.endsWith(".m4a") || lower.endsWith(".mp4") || lower.endsWith(".aac")) return "audio/mp4";
  if (lower.endsWith(".webm")) return "audio/webm";
  return fallback;
}

function numberOrNull(value: string): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function currentTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function languageLabel(code: string) {
  return languages.find((item) => item.code === code)?.label || code;
}
