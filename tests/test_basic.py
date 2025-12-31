from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_stats_ok():
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "messages" in data
    assert "documents" in data
    assert "chunks" in data
