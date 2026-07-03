import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
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

import { apiBaseUrl, sendWhatsAppMessage } from "@/api/client";
import { languages } from "@/constants/languages";
import type { ChatMessage, WhatsAppPayload } from "@/types/chat";

const green = "#075e54";
const accent = "#128c4a";
const cream = "#f7f5ee";
const line = "#dfe4dc";

export default function IndexScreen() {
  const [phone, setPhone] = useState("");
  const [language, setLanguage] = useState("hi-IN");
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
            Alert.alert("Phone number required", "Enter farmer phone number to start.");
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

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      style={{ flex: 1, backgroundColor: cream }}
      contentContainerStyle={{
        minHeight: "100%",
        paddingTop: insets.top + 28,
        paddingBottom: insets.bottom + 24,
        paddingHorizontal: 22,
        gap: 22,
      }}
    >
      <View style={{ gap: 10 }}>
        <View
          style={{
            width: 62,
            height: 62,
            borderRadius: 18,
            backgroundColor: accent,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text selectable={false} style={{ color: "#fff", fontSize: 18, fontWeight: "900" }}>
            KA
          </Text>
        </View>
        <Text selectable style={{ fontSize: 34, fontWeight: "900", color: "#182018" }}>
          Kisan Alert
        </Text>
        <Text selectable style={{ color: "#5f6d5f", fontSize: 16, lineHeight: 22 }}>
          Start a smart water, crop and advisory conversation in the farmer language.
        </Text>
      </View>

      <View style={{ gap: 10 }}>
        <Text selectable style={{ fontWeight: "800", color: "#263426" }}>
          Phone number
        </Text>
        <TextInput
          value={phone}
          onChangeText={onPhoneChange}
          keyboardType="phone-pad"
          placeholder="9999999999"
          style={{
            minHeight: 52,
            borderWidth: 1,
            borderColor: line,
            borderRadius: 12,
            paddingHorizontal: 14,
            backgroundColor: "#fff",
            fontSize: 17,
          }}
        />
      </View>

      <View style={{ gap: 10 }}>
        <Text selectable style={{ fontWeight: "800", color: "#263426" }}>
          Language
        </Text>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 9 }}>
          {languages.map((item) => {
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
                  borderColor: selected ? accent : line,
                  backgroundColor: selected ? "#e4f4e8" : "#fff",
                }}
              >
                <Text selectable={false} style={{ color: selected ? accent : "#243024", fontWeight: "700" }}>
                  {item.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={{ flex: 1 }} />
      <Pressable
        onPress={onStart}
        style={{
          minHeight: 54,
          borderRadius: 14,
          backgroundColor: accent,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Text selectable={false} style={{ color: "#fff", fontWeight: "900", fontSize: 16 }}>
          Start Conversation
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
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      text: "Namaste. Ask about irrigation, crop recommendation, or crop health.",
      mine: false,
    },
  ]);

  useEffect(() => {
    scrollRef.current?.scrollToEnd({ animated: true });
  }, [messages.length]);

  async function sendPayload(userText: string, payload: WhatsAppPayload) {
    setMessages((current) => [
      ...current,
      { id: `${Date.now()}-user`, text: userText, mine: true },
    ]);
    setSending(true);
    try {
      const response = await sendWhatsAppMessage(payload);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          text: response.reply,
          mine: false,
          intent: response.intent,
        },
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Backend request failed.";
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-error`,
          text: `Could not reach backend at ${apiBaseUrl}. ${message}`,
          mine: false,
          intent: "error",
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
    sendPayload(text, {
      from_phone: phone,
      language,
      text,
    });
  }

  async function shareLocation() {
    if (sending) return;
    const permission = await Location.requestForegroundPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Location permission needed", "Allow location to share the farm point.");
      return;
    }
    const position = await Location.getCurrentPositionAsync({});
    await sendPayload("Shared current farm location", {
      from_phone: phone,
      language,
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      location_label: "Shared from React Native app",
    });
  }

  async function attachPhoto(useCamera: boolean) {
    if (sending) return;
    const permission = useCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Photo permission needed", "Allow photo access to send a crop image.");
      return;
    }

    const result = useCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.7, base64: true })
      : await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          quality: 0.7,
          base64: true,
        });

    if (result.canceled || !result.assets[0]) return;
    const asset = result.assets[0];
    await sendPayload("Crop photo attached", {
      from_phone: phone,
      language,
      text: input.trim() || "crop photo for diagnosis",
      media_type: "image",
      media_base64: asset.base64 ?? undefined,
      media_uri: asset.base64 ? undefined : asset.uri,
      media_mime_type: asset.mimeType || "image/jpeg",
    });
    setInput("");
  }

  function sendVoiceTranscript() {
    const transcript = input.trim() || "Should I irrigate today?";
    setInput("");
    sendPayload(`Voice note: ${transcript}`, {
      from_phone: phone,
      language,
      text: transcript,
      media_type: "voice",
    });
  }

  const maxBubbleWidth = Math.min(width * 0.78, 620);

  return (
    <KeyboardAvoidingView
      behavior={Platform.select({ ios: "padding", default: undefined })}
      style={{ flex: 1, backgroundColor: cream }}
    >
      <View
        style={{
          paddingTop: insets.top + 10,
          paddingHorizontal: 14,
          paddingBottom: 12,
          backgroundColor: green,
          flexDirection: "row",
          alignItems: "center",
          gap: 12,
        }}
      >
        <View
          style={{
            width: 44,
            height: 44,
            borderRadius: 22,
            backgroundColor: accent,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text selectable={false} style={{ color: "#fff", fontSize: 13, fontWeight: "900" }}>
            KA
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text selectable style={{ color: "#fff", fontSize: 18, fontWeight: "900" }}>
            Kisan Alert
          </Text>
          <Text selectable style={{ color: "#cfebe1", fontSize: 12 }}>
            Backend: {apiBaseUrl}
          </Text>
        </View>
        <LanguageMenu value={language} onChange={onLanguageChange} />
      </View>

      <ScrollView
        ref={scrollRef}
        contentInsetAdjustmentBehavior="automatic"
        keyboardShouldPersistTaps="handled"
        style={{ flex: 1 }}
        contentContainerStyle={{ padding: 14, gap: 8 }}
      >
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} maxWidth={maxBubbleWidth} />
        ))}
      </ScrollView>

      {sending ? <ActivityIndicator style={{ paddingVertical: 6 }} color={accent} /> : null}

      <View
        style={{
          paddingBottom: insets.bottom + 8,
          paddingTop: 8,
          paddingHorizontal: 8,
          backgroundColor: "#fff",
          borderTopWidth: 1,
          borderTopColor: line,
          gap: 8,
        }}
      >
        <View style={{ flexDirection: "row", gap: 6 }}>
          <ToolButton label="Map" onPress={shareLocation} disabled={sending} />
          <ToolButton label="Camera" onPress={() => attachPhoto(true)} disabled={sending} />
          <ToolButton label="Photo" onPress={() => attachPhoto(false)} disabled={sending} />
          <ToolButton label="Voice" onPress={sendVoiceTranscript} disabled={sending} />
        </View>
        <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 8 }}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Type or describe crop photo / voice note..."
            multiline
            style={{
              flex: 1,
              minHeight: 44,
              maxHeight: 120,
              borderWidth: 1,
              borderColor: line,
              borderRadius: 22,
              paddingHorizontal: 14,
              paddingVertical: 10,
              fontSize: 16,
              backgroundColor: "#f9fbf7",
            }}
          />
          <Pressable
            onPress={sendText}
            disabled={sending}
            style={{
              width: 46,
              height: 46,
              borderRadius: 23,
              backgroundColor: sending ? "#8dbb9b" : accent,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Text selectable={false} style={{ color: "#fff", fontSize: 18, fontWeight: "900" }}>
              ➤
            </Text>
          </Pressable>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

function LanguageMenu({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxWidth: 112 }}>
      <View style={{ flexDirection: "row", gap: 6 }}>
        {languages.map((item) => {
          const selected = item.code === value;
          return (
            <Pressable
              key={item.code}
              onPress={() => onChange(item.code)}
              style={{
                paddingHorizontal: 10,
                paddingVertical: 7,
                borderRadius: 999,
                backgroundColor: selected ? "#e7fff1" : "rgba(255,255,255,0.16)",
              }}
            >
              <Text selectable={false} style={{ color: selected ? green : "#fff", fontWeight: "800" }}>
                {item.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </ScrollView>
  );
}

function ToolButton({
  label,
  onPress,
  disabled,
}: {
  label: string;
  onPress: () => void;
  disabled: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={{
        flex: 1,
        minHeight: 36,
        borderRadius: 18,
        backgroundColor: "#eef6ef",
        alignItems: "center",
        justifyContent: "center",
        borderWidth: 1,
        borderColor: "#d5e6d6",
        opacity: disabled ? 0.55 : 1,
      }}
    >
      <Text selectable={false} style={{ color: green, fontWeight: "800", fontSize: 12 }}>
        {label}
      </Text>
    </Pressable>
  );
}

function MessageBubble({
  message,
  maxWidth,
}: {
  message: ChatMessage;
  maxWidth: number;
}) {
  return (
    <View style={{ alignItems: message.mine ? "flex-end" : "flex-start" }}>
      <View
        style={{
          maxWidth,
          paddingHorizontal: 13,
          paddingVertical: 10,
          borderRadius: 13,
          backgroundColor: message.mine ? "#d9fdd3" : "#fff",
          borderTopRightRadius: message.mine ? 4 : 13,
          borderTopLeftRadius: message.mine ? 13 : 4,
          borderWidth: 1,
          borderColor: message.mine ? "#c9edc3" : "#ecefeb",
        }}
      >
        <Text selectable style={{ fontSize: 15.5, color: "#172017", lineHeight: 21 }}>
          {message.text}
        </Text>
        {message.intent ? (
          <Text selectable style={{ marginTop: 6, fontSize: 11, color: "#687568" }}>
            {message.intent}
          </Text>
        ) : null}
      </View>
    </View>
  );
}
