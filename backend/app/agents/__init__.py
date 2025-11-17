from .base_agent import BaseAgent, AgentRegistry, agent_registry
from .orchestrator import OrchestratorAgent, orchestrator
from .marketing_agent import MarketingAgent
from .frontend_agent import FrontendDeveloperAgent
from .backend_agent import BackendDeveloperAgent

# Export OrchestratorAgent as both Orchestrator (for tests) and OrchestratorAgent
Orchestrator = OrchestratorAgent

__all__ = [
    "BaseAgent",
    "AgentRegistry",
    "agent_registry",
    "Orchestrator",
    "OrchestratorAgent",
    "orchestrator",
    "MarketingAgent",
    "FrontendDeveloperAgent",
    "BackendDeveloperAgent",
]