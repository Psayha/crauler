"""Test HR Agent functionality."""
import pytest
from httpx import AsyncClient

from app.agents.hr_agent import HRAgent


def test_hr_agent_creation():
    """Test HR Agent can be created."""
    hr_agent = HRAgent()
    
    assert hr_agent is not None
    assert hr_agent.get_agent_type() == "hr_manager"
    assert hr_agent.get_temperature() == 0.4


def test_hr_agent_temperature():
    """Test HR Agent has appropriate temperature."""
    hr_agent = HRAgent()
    
    # HR Agent should have balanced temperature for analysis and creativity
    assert 0.3 <= hr_agent.get_temperature() <= 0.5


@pytest.mark.asyncio
async def test_hr_agent_endpoints_exist(client: AsyncClient):
    """Test that HR Agent endpoints are available."""
    # Test performance endpoint
    response = await client.get("/api/hr/agents/performance")
    assert response.status_code == 200
    
    data = response.json()
    assert "agents" in data
    assert "time_period" in data


@pytest.mark.asyncio
async def test_hr_dynamic_agents_endpoint(client: AsyncClient):
    """Test dynamic agents listing endpoint."""
    response = await client.get("/api/hr/dynamic-agents")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "dynamic_agents" in data
    assert "total" in data
    assert isinstance(data["dynamic_agents"], list)

