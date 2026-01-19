import pytest
from src.server.app import app


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestRenderEndpoint:
    def test_render_endpoint_exists(self, client):
        """Server should have /render/<display_id> endpoint"""
        response = client.get("/render/kitchen")
        assert response.status_code == 200

    def test_render_endpoint_exists(self, client):
        """Server should have /render/<display_id> endpoint"""
        response = client.get("/render/kitchen")
        assert response.status_code == 200

    def test_render_returns_png(self, client):
        """Endpoint should return PNG image"""
        response = client.get("/render/kitchen")
        assert response.content_type == "image/png"

    def test_render_returns_valid_image(self, client):
        """Returned PNG should have valid PNG magic bytes"""
        response = client.get("/render/kitchen")
        assert len(response.data) > 0
        # PNG magic bytes
        assert response.data[:8] == b"\x89PNG\r\n\x1a\n"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
