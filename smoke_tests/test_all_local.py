import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
scripts = [
    "test_gemini.py",
    "test_firestore.py",
    "test_storage.py",
    "test_speech_to_text.py",
    "test_text_to_speech.py",
    "test_translation.py",
    "test_bigquery.py",
    "test_pubsub.py",
    "test_secret_manager.py",
    "test_dialogflow.py",
    "test_earth_engine.py",
    "test_maps_geocoding.py",
]

for script in scripts:
    print(f"\n--- {script} ---")
    result = subprocess.run([sys.executable, str(ROOT / "smoke_tests" / script)], cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

