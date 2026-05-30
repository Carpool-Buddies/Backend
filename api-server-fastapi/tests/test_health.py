from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest


@pytest.fixture
def client():
    with patch("app.core.database.create_db_and_tables"):
        with patch("app.core.config.Settings.__init__", return_value=None):
            with patch("app.core.config.Settings.SECRET_KEY", "test-secret", create=True):
                with patch("app.core.config.Settings.DATABASE_URL", "sqlite:///./test.db", create=True):
                    with patch("app.core.config.Settings.FRONTEND_URL", "http://localhost:3000", create=True):
                        from app.main import app
                        return TestClient(app)


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
