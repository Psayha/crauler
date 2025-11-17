"""Test AI agents."""
import pytest
from httpx import AsyncClient

from app.agents.base_agent import AgentRegistry
from app.agents.orchestrator import Orchestrator
from app.agents.marketing_agent import MarketingAgent
from app.agents.frontend_agent import FrontendDeveloperAgent
from app.agents.backend_agent import BackendDeveloperAgent


def test_import_all_agents():
    """Test all agents can be imported."""
    assert AgentRegistry is not None
    assert Orchestrator is not None
    assert MarketingAgent is not None
    assert FrontendDeveloperAgent is not None
    assert BackendDeveloperAgent is not None


def test_agent_registry():
    """Test agent registry has all agents."""
    registry = AgentRegistry()

    # Check that agents are registered
    assert len(registry.agents) > 0

    # Check specific agent types
    agent_types = [agent.get_agent_type() for agent in registry.agents.values()]

    expected_types = [
        "marketing",
        "frontend_developer",
        "backend_developer",
        "data_analyst",
        "ux_designer",
        "content_writer",
        "mobile_developer",
        "devops_engineer",
        "project_manager",
        "qa_engineer",
    ]

    for expected_type in expected_types:
        assert expected_type in agent_types, f"Agent type {expected_type} not found"


def test_agent_temperatures():
    """Test agents have appropriate temperature settings."""
    registry = AgentRegistry()

    for agent in registry.agents.values():
        temperature = agent.get_temperature()

        # Temperature should be between 0 and 1
        assert 0 <= temperature <= 1, f"Agent {agent.get_agent_type()} has invalid temperature: {temperature}"

        # DevOps should have lowest temperature (most deterministic)
        if agent.get_agent_type() == "devops_engineer":
            assert temperature <= 0.3, "DevOps agent should have low temperature"

        # Marketing should have higher temperature (more creative)
        if agent.get_agent_type() == "marketing":
            assert temperature >= 0.4, "Marketing agent should have higher temperature"


def test_orchestrator_creation():
    """Test orchestrator can be created."""
    orchestrator = Orchestrator()

    assert orchestrator is not None
    assert orchestrator.get_agent_type() == "orchestrator"
    assert orchestrator.get_temperature() == 0.5


@pytest.mark.asyncio
async def test_agents_endpoint(client: AsyncClient):
    """Test agents API endpoint."""
    response = await client.get("/api/agents")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 10  # Should have 10 agents

    # Check agent structure
    for agent in data:
        assert "type" in agent
        assert "name" in agent
        assert "description" in agent
        assert "temperature" in agent


@pytest.mark.asyncio
async def test_specific_agent_endpoint(client: AsyncClient):
    """Test getting specific agent info."""
    response = await client.get("/api/agents/marketing")

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "marketing"
    assert "name" in data
    assert "description" in data
    assert "expertise" in data
