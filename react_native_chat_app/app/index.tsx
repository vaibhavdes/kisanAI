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
  Platform,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  useWindowDimensions,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { apiBaseUrl, sendChatMessage } from "@/api/client";
import { languages } from "@/constants/languages";
import type { ChatMessage, ChatPayload, ChatResponse } from "@/types/chat";

const whatsAppGreen = "#075e54";
const whatsAppLightGreen = "#128c7e";
const bubbleMine = "#dcf8c6";
const bubbleTheirs = "#ffffff";
const wallpaper = "#efe7da";
const border = "#d9d4c8";
const autoLanguageCode = "auto";

export default function IndexScreen() {
  const [phone, setPhone] = useState("");
  const [language, setLanguage] = useState(autoLanguageCode);
  const [started, setStarted] = useState(false);

  if (!started) {
    return (
      <OnboardingScreen
        phone={phone}
        language={language}
        onPhoneChange={setPhone}
        onLanguageChange={setLanguage}
        onStart={() => {
          if (!phone.trim()) {
            Alert.alert("Phone number required", "Enter the farmer phone number to start.");
            return;
          }
          setStarted(true);
        }}
      />
    );
  }

  return <ChatScreen phone={phone.trim()} language={language} onLanguageChange={setLanguage} />;
}

function OnboardingScreen({
  phone,
  language,
  onPhoneChange,
  onLanguageChange,
  onStart,
}: {
  phone: string;
  language: string;
  onPhoneChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onStart: () => void;
}) {
  const insets = useSafeAreaInsets();
  const languageOptions = [{ code: autoLanguageCode, label: "Auto" }, ...languages];

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
            KA
          </Text>
        </View>
        <Text selectable style={{ fontSize: 34, fontWeight: "900", color: "#172017" }}>
          Kisan Alert
        </Text>
        <Text selectable style={{ color: "#526052", fontSize: 16, lineHeight: 23 }}>
          WhatsApp-style farmer advisory chat for voice, photos, location and SMS-ready support.
        </Text>
      </View>

      <View style={{ gap: 10 }}>
        <Text selectable style={{ fontWeight: "800", color: "#263426" }}>
          Farmer phone
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
          Reply language
        </Text>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 9 }}>
          {languageOptions.map((item) => {
            const selected = language === item.code;
            return (
              <Pressable
                key={item.code}
                onPress={() => onLanguageChange(item.code)}
                style={{
                  paddingHorizontal: 14,
                  paddingVertical: 10,
                  borderRadius: 999,
                  borderWidth: 1,
                  borderColor: selected ? whatsAppLightGreen : border,
                  backgroundColor: selected ? "#dff4eb" : "#fff",
                }}
              >
                <Text selectable={false} style={{ color: selected ? whatsAppGreen : "#263426", fontWeight: "800" }}>
                  {item.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <Text selectable style={{ color: "#667266", fontSize: 12, lineHeight: 17 }}>
          Auto lets the backend detect the farmer language from text when Google Translation is enabled.
        </Text>
      </View>

      <View style={{ flex: 1 }} />
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
          Start chat
        </Text>
      </Pressable>
    </ScrollView>
  );
}

function ChatScreen({
  phone,
  language,
  onLanguageChange,
}: {
  phone: string;
  language: string;
  onLanguageChange: (value: string) => void;
}) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const scrollRef = useRef<ScrollView>(null);
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recorderState = useAudioRecorderState(audioRecorder);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [attachmentsOpen, setAttachmentsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      text: "Namaste. Send a message, crop photo, voice note, or farm location.",
      mine: false,
      kind: "system",
      time: currentTime(),
    },
  ]);

  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [messages.length]);

  function payloadLanguage() {
    return language === autoLanguageCode ? undefined : language;
  }

  async function sendPayload(userMessage: ChatMessage, payload: ChatPayload) {
    const localId = userMessage.id;
    setMessages((current) => [...current, { ...userMessage, status: "sending", time: currentTime() }]);
    setSending(true);
    try {
      const response = await sendChatMessage({ ...payload, language: payloadLanguage() });
      setMessages((current) =>
        current.map((message) => (message.id === localId ? { ...message, status: "sent" } : message)),
      );
      setMessages((current) => [...current, responseToMessage(response)]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Backend request failed.";
      setMessages((current) =>
        current.map((item) => (item.id === localId ? { ...item, status: "failed" } : item)),
      );
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-error`,
          text: `Could not reach backend at ${apiBaseUrl}. ${message}`,
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
      Alert.alert("Location permission needed", "Allow location to share the farm point.");
      return;
    }
    const position = await Location.getCurrentPositionAsync({});
    const coords = `${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`;
    await sendPayload(
      {
        id: `${Date.now()}-location`,
        text: `Farm location shared\n${coords}`,
        mine: true,
        kind: "location",
      },
      {
        from_phone: phone,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        location_label: "Shared from Kisan Alert app",
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
      Alert.alert("Photo permission needed", "Allow photo access to send a crop image.");
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
    const caption = input.trim() || "Crop photo for diagnosis";
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
        media_base64: asset.base64 ?? undefined,
        media_uri: asset.base64 ? undefined : asset.uri,
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
      Alert.alert("Microphone permission needed", "Allow microphone access to send a voice note.");
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
      Alert.alert("Voice note failed", "Recording finished but no audio file was created.");
      return;
    }
    const typedCaption = input.trim();
    const base64 = await uriToBase64(uri);
    setInput("");
    await sendPayload(
      {
        id: `${Date.now()}-audio`,
        text: typedCaption || voiceDurationLabel(recorderState.durationMillis),
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
            KA
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text selectable style={{ color: "#fff", fontSize: 17, fontWeight: "900" }} numberOfLines={1}>
            Kisan Alert
          </Text>
          <Text selectable style={{ color: "#d4eee8", fontSize: 12 }} numberOfLines={1}>
            {phone} · {language === autoLanguageCode ? "Auto language" : languageLabel(language)}
          </Text>
        </View>
        <LanguageMenu value={language} onChange={onLanguageChange} />
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
          <MessageBubble key={message.id} message={message} maxWidth={maxBubbleWidth} />
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
          <AttachmentAction label="Camera" icon="📷" onPress={() => attachPhoto(true)} />
          <AttachmentAction label="Gallery" icon="🖼" onPress={() => attachPhoto(false)} />
          <AttachmentAction label="Location" icon="📍" onPress={shareLocation} />
        </View>
      ) : null}

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
            placeholder={recorderState.isRecording ? "Recording voice note..." : "Message"}
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

function LanguageMenu({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const languageOptions = [{ code: autoLanguageCode, label: "Auto" }, ...languages];
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxWidth: 104 }}>
      <View style={{ flexDirection: "row", gap: 6 }}>
        {languageOptions.map((item) => {
          const selected = item.code === value;
          return (
            <Pressable
              key={item.code}
              onPress={() => onChange(item.code)}
              style={{
                paddingHorizontal: 9,
                paddingVertical: 7,
                borderRadius: 999,
                backgroundColor: selected ? "#e7fff1" : "rgba(255,255,255,0.16)",
              }}
            >
              <Text selectable={false} style={{ color: selected ? whatsAppGreen : "#fff", fontWeight: "800" }}>
                {item.label}
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

function MessageBubble({ message, maxWidth }: { message: ChatMessage; maxWidth: number }) {
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
              Farm location
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
              Voice
            </Text>
          </Pressable>
        ) : null}

        {message.text ? (
          <Text selectable style={{ fontSize: isSystem ? 12 : 15.5, color: "#172017", lineHeight: isSystem ? 17 : 21 }}>
            {message.text}
          </Text>
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

function responseToMessage(response: ChatResponse): ChatMessage {
  const audioUri =
    response.response_audio_base64 && response.response_audio_content_type
      ? `data:${response.response_audio_content_type};base64,${response.response_audio_base64}`
      : undefined;
  return {
    id: `${Date.now()}-assistant`,
    text: response.transcript ? `${response.reply}\n\nHeard: ${response.transcript}` : response.reply,
    mine: false,
    kind: audioUri ? "audio" : "text",
    audioUri,
    audioContentType: response.response_audio_content_type,
    intent: response.intent,
    status: "sent",
    time: currentTime(),
  };
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

function audioMimeType(uri: string) {
  const lower = uri.toLowerCase();
  if (lower.endsWith(".wav")) return "audio/wav";
  if (lower.endsWith(".mp3")) return "audio/mpeg";
  if (lower.endsWith(".ogg") || lower.endsWith(".oga")) return "audio/ogg";
  if (lower.endsWith(".m4a") || lower.endsWith(".mp4")) return "audio/mp4";
  return "audio/mpeg";
}

function voiceDurationLabel(durationMillis: number) {
  const seconds = Math.max(1, Math.round(durationMillis / 1000));
  return `Voice note ${seconds}s`;
}

function currentTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function languageLabel(code: string) {
  return languages.find((item) => item.code === code)?.label || code;
}
