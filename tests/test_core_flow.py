from fastapi.testclient import TestClient

from app.main import app
from app.repositories.memory_store import store

client = TestClient(app)


def setup_function() -> None:
    store.reset()


def create_demo_farmer() -> str:
    response = client.post(
        "/api/v1/farmers",
        json={
            "name": "Ravi",
            "phone": "9999999999",
            "language": "te-IN",
            "village": "Demo Village",
            "district": "Guntur",
            "state": "Andhra Pradesh",
            "farm": {
                "area_acres": 2.5,
                "soil_type": "black",
                "soil_ph": 6.8,
                "groundwater_depth_m": 18,
                "latitude": 16.3,
                "longitude": 80.4,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_end_to_end_farmer_advisory_and_diagnosis_flow() -> None:
    farmer_id = create_demo_farmer()

    crop_response = client.post(
        "/api/v1/recommendations/crop",
        json={
            "farmer_id": farmer_id,
            "season": "kharif",
            "expected_rainfall_mm": 620,
            "water_availability": "medium",
        },
    )
    assert crop_response.status_code == 200
    assert len(crop_response.json()["recommendations"]) == 3

    advisory_response = client.post(
        "/api/v1/advisories/dry-spell",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "soil_moisture": 0.18,
            "rainfall_forecast_mm": [0, 0, 0, 1, 0, 0, 3],
            "temperature_c": 36,
        },
    )
    assert advisory_response.status_code == 200
    assert advisory_response.json()["risk_level"] in {"high", "critical"}

    diagnosis_response = client.post(
        "/api/v1/diagnosis/log",
        json={
            "farmer_id": farmer_id,
            "crop": "chilli",
            "symptoms_text": "Leaves curling and white insects visible",
            "photo_uri": "gs://demo/chilli-leaf.jpg",
        },
    )
    assert diagnosis_response.status_code == 200
    assert diagnosis_response.json()["expert_ticket"]["status"] == "open"

    tickets_response = client.get(f"/api/v1/expert/tickets/{farmer_id}")
    assert tickets_response.status_code == 200
    assert len(tickets_response.json()) == 1

    stage_response = client.post(
        "/api/v1/advisories/crop-stage",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "stage": "flowering",
            "rainfall_forecast_mm": [0, 0, 0, 0, 1, 0, 2],
            "humidity_percent": 88,
            "soil_moisture": 0.19,
        },
    )
    assert stage_response.status_code == 200
    assert stage_response.json()["alert_plan"]["channels"]


def test_low_connectivity_channels_accept_farmer_intent() -> None:
    sms_response = client.post(
        "/api/v1/sms/webhook",
        json={"from_phone": "9999999999", "text": "WATER maize 522001", "language": "hi-IN"},
    )
    assert sms_response.status_code == 200
    assert sms_response.json()["intent"] == "irrigation_advisory"

    whatsapp_response = client.post(
        "/api/v1/whatsapp/webhook",
        json={
            "from_phone": "9999999999",
            "text": "my crop leaf has spots",
            "language": "en-IN",
        },
    )
    assert whatsapp_response.status_code == 200
    assert whatsapp_response.json()["intent"] == "crop_diagnosis"

    call_response = client.post(
        "/api/v1/calls/webhook",
        json={
            "from_phone": "9999999999",
            "call_id": "demo-call-1",
            "dtmf_digit": "2",
            "language": "te-IN",
        },
    )
    assert call_response.status_code == 200
    assert call_response.json()["intent"] == "crop_recommendation"


def test_extension_interfaces_for_data_soil_and_conversation() -> None:
    farmer_id = create_demo_farmer()

    sources_response = client.get("/api/v1/data/sources")
    assert sources_response.status_code == 200
    assert any("IMD" in f'{item["name"]} {item["provider"]}' for item in sources_response.json())

    context_response = client.post(
        "/api/v1/data/context",
        json={"state": "Andhra Pradesh", "district": "Guntur", "crop": "chilli", "season": "kharif"},
    )
    assert context_response.status_code == 200
    assert context_response.json()["recommended_datasets"]

    soil_response = client.post(
        "/api/v1/soil-cards/extract",
        json={
            "farmer_id": farmer_id,
            "extracted_text": "pH 6.8 EC 0.42 organic carbon 0.55 nitrogen medium phosphorus 18 potassium high",
        },
    )
    assert soil_response.status_code == 200
    assert soil_response.json()["ph"] == 6.8

    log_response = client.post(
        "/api/v1/conversations/log",
        json={
            "farmer_id": farmer_id,
            "role": "farmer",
            "text": "Should I irrigate today?",
            "language": "en-IN",
            "channel": "whatsapp",
            "intent": "irrigation_advisory",
        },
    )
    assert log_response.status_code == 200
    assert log_response.json()["saved"] is True

    recent_response = client.get(f"/api/v1/conversations/{farmer_id}")
    assert recent_response.status_code == 200
    assert len(recent_response.json()) == 1
