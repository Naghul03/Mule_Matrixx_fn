from unittest.mock import MagicMock
from app.db.session import get_db
from app.main import create_application
from fastapi.testclient import TestClient


def test_service_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mule-matrix-backend"
    assert data["version"] == "0.1.0"
    assert "environment" in data


def test_database_health_success(client):
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["database"] == "mule_matrix"
    assert data["latency_ms"] is not None
    assert data["error"] is None


def test_database_health_failure_handling():
    app = create_application()

    # Mock a database session that raises an exception on query execution
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Simulated connection dropped")

    def override_get_db_failure():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db_failure

    with TestClient(app) as broken_client:
        response = broken_client.get("/api/v1/health/database")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "disconnected"
        assert "Database connectivity check failed" in data["error"]

