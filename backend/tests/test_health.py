"""Test health and basic API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns correct info."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "operational"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data


@pytest.mark.asyncio
async def test_docs_endpoint(client: AsyncClient):
    """Test API documentation is accessible."""
    response = await client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


@pytest.mark.asyncio
async def test_redoc_endpoint(client: AsyncClient):
    """Test ReDoc documentation is accessible."""
    response = await client.get("/redoc")

    assert response.status_code == 200
    assert "redoc" in response.text.lower()


@pytest.mark.asyncio
async def test_openapi_json(client: AsyncClient):
    """Test OpenAPI schema is available."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()

    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
