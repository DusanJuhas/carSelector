from fastapi.testclient import TestClient

from tests.conftest import SeededData


def test_list_brands(client: TestClient):
    response = client.get("/api/brands")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [{"id": 1, "name": "Mazda", "slug": "mazda"}]


def test_list_vehicles_returns_seeded_configurations(client: TestClient):
    response = client.get("/api/vehicles")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    trims = {item["trim"] for item in body["items"]}
    assert trims == {"Prime-Line", "Centre-Line"}
    prime = next(item for item in body["items"] if item["trim"] == "Prime-Line")
    assert prime["price"] == {"amount": 824900.0, "currency": "CZK"}
    assert prime["match_score"] is None
    assert prime["flag"] is None


def test_list_vehicles_filters_by_drivetrain(client: TestClient):
    response = client.get("/api/vehicles", params={"drivetrain": "awd"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["trim"] == "Centre-Line"


def test_list_vehicles_filters_by_budget_and_currency(client: TestClient):
    response = client.get("/api/vehicles", params={"budget_max": 900_000, "currency": "CZK"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["trim"] == "Prime-Line"


def test_get_vehicle_detail(client: TestClient, seeded_session: SeededData):
    response = client.get(f"/api/vehicles/{seeded_session.config_prime_2wd_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["brand"] == "Mazda"
    assert body["model"] == "CX-5"
    assert body["powertrain"]["drivetrain"] == "fwd"
    assert body["powertrain"]["consumption_min"] == 7.0
    assert body["colors"] == [
        {"name": "Arctic White", "finish_type": "solid", "surcharge": {"amount": 0.0, "currency": "CZK"}}
    ]
    assert body["standard_equipment"] == ["17-inch alloy wheels"]
    assert body["optional_equipment"] == []
    assert len(body["price_history"]) == 1
    assert body["price_history"][0]["lowest_price_30d"] == {"amount": 875900.0, "currency": "CZK"}


def test_get_vehicle_detail_404(client: TestClient):
    response = client.get("/api/vehicles/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "vehicle_not_found"


def test_compare_vehicles(client: TestClient, seeded_session: SeededData):
    ids = f"{seeded_session.config_prime_2wd_id},{seeded_session.config_centre_awd_id}"
    response = client.get("/api/vehicles/compare", params={"ids": ids})
    assert response.status_code == 200
    body = response.json()
    assert len(body["vehicles"]) == 2


def test_compare_vehicles_rejects_too_few_ids(client: TestClient, seeded_session: SeededData):
    response = client.get("/api/vehicles/compare", params={"ids": str(seeded_session.config_prime_2wd_id)})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_id_count"


def test_compare_vehicles_reports_missing_ids(client: TestClient, seeded_session: SeededData):
    ids = f"{seeded_session.config_prime_2wd_id},999999"
    response = client.get("/api/vehicles/compare", params={"ids": ids})
    assert response.status_code == 404
    assert response.json()["error"]["details"]["missing_ids"] == [999999]


def test_model_overview(client: TestClient, seeded_session: SeededData):
    response = client.get(f"/api/models/{seeded_session.model_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["brand"] == "Mazda"
    assert body["model"] == "CX-5"
    assert body["category"] == "SUV"
    trim_names = {trim["name"] for trim in body["trims"]}
    assert trim_names == {"Prime-Line", "Centre-Line"}


def test_model_overview_404(client: TestClient):
    response = client.get("/api/models/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "model_not_found"


def test_start_conversation(client: TestClient):
    response = client.post("/api/conversations")
    assert response.status_code == 201
    body = response.json()
    assert "conversation_id" in body
    assert "intro_message" in body


def test_send_message_unknown_conversation(client: TestClient):
    response = client.post("/api/conversations/does-not-exist/messages", json={"text": "hi"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "conversation_not_found"


def test_send_message_without_api_key_returns_503(client: TestClient):
    # No ANTHROPIC_API_KEY is configured in this environment - confirms
    # the AI layer fails loudly (503), not silently or with a 500.
    start = client.post("/api/conversations")
    conversation_id = start.json()["conversation_id"]
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"text": "We're a family of 4 heading to the mountains most weekends."},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_not_configured"
