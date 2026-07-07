from common import optional_env, print_ok, require_env, require_package

require_package("google.genai", "pip install -r requirements.txt")

from google import genai


api_key = require_env("GEMINI_API_KEY")
model = optional_env("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=api_key)

prompt = """
You are KISAN-AI, an agricultural advisory assistant.

Give a short Marathi advisory for a cotton farmer before heavy rain.
Use simple farmer-friendly language.
Mention what to avoid and what action to take.
"""

response = client.models.generate_content(model=model, contents=prompt)
print(response.text)
print_ok(f"Gemini responded using {model}")
