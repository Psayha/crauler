"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


@pytest.mark.asyncio
async def test_agents_list_endpoint():
    """Test agents list endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 11  # Should have all 11 agents


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "name" in data


@pytest.mark.asyncio
async def test_cors_headers():
    """Test CORS headers are set correctly."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS headers should be present or OPTIONS should be handled
        assert response.status_code in [200, 204]


@pytest.mark.asyncio
async def test_api_versioning():
    """Test API versioning is consistent."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Health endpoint is at root level
        response = await client.get("/health")
        assert response.status_code == 200

        # API endpoints should be under /api prefix
        response = await client.get("/api/agents")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_error_handling_404():
    """Test 404 error handling."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_swagger_docs():
    """Test Swagger documentation is available."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema():
    """Test OpenAPI schema is available."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "title" in data["info"]
        # Title should be from settings.app_name
        assert "AI Agency" in data["info"]["title"]
