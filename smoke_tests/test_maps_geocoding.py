from common import print_ok, require_env, require_package

require_package("requests", "pip install -r requirements-google.txt")

import requests


api_key = require_env("MAPS_API_KEY")
response = requests.get(
    "https://maps.googleapis.com/maps/api/geocode/json",
    params={"address": "Pune, Maharashtra, India", "key": api_key},
    timeout=20,
)
response.raise_for_status()
data = response.json()
if data.get("status") != "OK":
    raise RuntimeError(f"Geocoding API status: {data.get('status')} - {data.get('error_message')}")
print_ok("Google Maps Geocoding responded")

