export type ChatMessage = {
  id: string;
  text: string;
  mine: boolean;
  kind?: "text" | "image" | "audio" | "location" | "system";
  mediaUri?: string;
  audioUri?: string;
  audioContentType?: string;
  intent?: string;
  status?: "sending" | "sent" | "failed";
  time?: string;
  dataSources?: Record<string, string | number | boolean | null | undefined>;
  serviceWarnings?: string[];
  storedContext?: Record<string, string | number | boolean | null | undefined>;
};

export type ChatPayload = {
  from_phone: string;
  text?: string;
  media_uri?: string;
  media_base64?: string;
  media_mime_type?: string;
  media_type?: string;
  audio_uri?: string;
  audio_base64?: string;
  audio_mime_type?: string;
  latitude?: number;
  longitude?: number;
  location_label?: string;
  language?: string;
};

export type ChatResponse = {
  reply: string;
  intent: string;
  farmer_id?: string;
  detected_language?: string;
  transcript?: string;
  response_audio_base64?: string;
  response_audio_content_type?: string;
  delivery_status?: string;
  missing_fields?: string[];
  data_sources?: Record<string, string | number | boolean | null | undefined>;
  service_warnings?: string[];
  stored_context?: Record<string, string | number | boolean | null | undefined>;
};
