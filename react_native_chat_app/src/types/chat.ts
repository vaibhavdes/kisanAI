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

export type SensorReadingPayload = {
  farmer_id: string;
  sensor_id: string;
  source: string;
  device_type: string;
  timestamp?: string;
  latitude?: number;
  longitude?: number;
  readings: {
    soil_moisture?: number | null;
    soil_temperature_c?: number | null;
    air_temperature_c?: number | null;
    humidity_percent?: number | null;
    rainfall_mm?: number | null;
    battery_percent?: number | null;
  };
};

export type SensorReadingResponse = {
  saved: boolean;
  advisory_hint: string;
  reading: {
    id: string;
    farmer_id: string;
    sensor_id: string;
    source: string;
    device_type: string;
    soil_moisture_risk: string;
  };
};

export type LiveTokenResponse = {
  ready: boolean;
  model: string;
  token?: string | null;
  note: string;
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
  media_url?: string;
  media_content_type?: string;
  delivery_status?: string;
  missing_fields?: string[];
  data_sources?: Record<string, string | number | boolean | null | undefined>;
  service_warnings?: string[];
  stored_context?: Record<string, string | number | boolean | null | undefined>;
};
