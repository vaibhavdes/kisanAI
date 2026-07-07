import binascii
import json
import struct
import zlib

from common import optional_env, print_ok, require_env, require_package

require_package("google.genai", "pip install -r requirements.txt")

from google import genai
from google.genai import types


project = require_env("GOOGLE_CLOUD_PROJECT")
location = optional_env("GOOGLE_CLOUD_LOCATION", "global")
model = optional_env("VERTEX_AI_MODEL", "gemini-2.5-flash")

client = genai.Client(vertexai=True, project=project, location=location)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)


def make_png(width: int = 8, height: int = 8) -> bytes:
    raw = b"".join(b"\x00" + b"\x4c\xa3\x57" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw))
        + png_chunk(b"IEND", b"")
    )


png_image = make_png()
response = client.models.generate_content(
    model=model,
    contents=[
        "Return only JSON with keys description and confidence for this image.",
        types.Part.from_bytes(data=png_image, mime_type="image/png"),
    ],
    config=types.GenerateContentConfig(response_mime_type="application/json"),
)
data = json.loads(response.text or "{}")
print(data)
print_ok(f"Vertex Vision responded using {model} in {location}")
