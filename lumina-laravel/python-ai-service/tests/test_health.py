"""
Tests for GET /api/v1/health
"""


class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_response_shape(self, client):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "ok"
        assert data["service"] == "lumina-ai"

    def test_health_no_auth_required(self, client):
        """Health endpoint must be reachable without a Bearer token."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_content_type(self, client):
        response = client.get("/api/v1/health")
        assert "application/json" in response.headers["content-type"]
