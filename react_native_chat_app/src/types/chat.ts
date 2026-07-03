export type ChatMessage = {
  id: string;
  text: string;
  mine: boolean;
  intent?: string;
};

export type WhatsAppPayload = {
  from_phone: string;
  text?: string;
  media_uri?: string;
  media_base64?: string;
  media_mime_type?: string;
  media_type?: string;
  latitude?: number;
  longitude?: number;
  location_label?: string;
  language: string;
};

export type WhatsAppResponse = {
  reply: string;
  intent: string;
  farmer_id?: string;
  detected_language?: string;
  delivery_status?: string;
};
