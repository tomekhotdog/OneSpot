from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_bays():
    response = client.get("/api/map/bays")
    assert response.status_code == 200
    data = response.json()
    assert "bays" in data
    assert "levels" in data
    assert len(data["bays"]) == 150


def test_unknown_api_route():
    response = client.get("/api/nonexistent")
    assert response.status_code in (404, 405)
