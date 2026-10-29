from fastapi.testclient import TestClient
from risk_agent.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_validation():
    assert client.post("/analyze", json={"company": "", "question": "short"}).status_code == 422


def test_sources():
    response = client.get("/sources")
    assert response.status_code == 200
    assert len(response.json()) >= 3
