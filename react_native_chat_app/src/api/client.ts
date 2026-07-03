import type { WhatsAppPayload, WhatsAppResponse } from "@/types/chat";

const fallbackUrl = process.env.EXPO_PUBLIC_API_URL || "http://10.0.2.2:8080";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${fallbackUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = typeof data.detail === "string" ? data.detail : `HTTP ${response.status}`;
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export function sendWhatsAppMessage(payload: WhatsAppPayload): Promise<WhatsAppResponse> {
  return postJson<WhatsAppResponse>("/api/v1/whatsapp/webhook", payload);
}

export const apiBaseUrl = fallbackUrl;
