"""
Agent Registry

Central registry for all AI agents in the system.
Provides easy access to agents by type.
"""

import logging
from typing import Optional, Dict, List
from app.agents.base_agent import BaseAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.marketing_agent import MarketingAgent
from app.agents.frontend_agent import FrontendDeveloperAgent
from app.agents.backend_agent import BackendDeveloperAgent
from app.agents.data_analyst_agent import DataAnalystAgent
from app.agents.ux_designer_agent import UXDesignerAgent
from app.agents.content_writer_agent import ContentWriterAgent
from app.agents.mobile_developer_agent import MobileDeveloperAgent
from app.agents.devops_engineer_agent import DevOpsEngineerAgent
from app.agents.project_manager_agent import ProjectManagerAgent
from app.agents.qa_engineer_agent import QAEngineerAgent
from app.agents.hr_agent import HRAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for all AI agents.

    Manages agent instances and provides access by agent type.
    """

    def __init__(self):
        """Initialize agent registry with all available agents."""
        self._agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agent instances."""
        logger.info("Initializing agent registry...")

        # Create instances of all agents
        agents_to_register = [
            OrchestratorAgent(),
            MarketingAgent(),
            FrontendDeveloperAgent(),
            BackendDeveloperAgent(),
            DataAnalystAgent(),
            UXDesignerAgent(),
            ContentWriterAgent(),
            MobileDeveloperAgent(),
            DevOpsEngineerAgent(),
            ProjectManagerAgent(),
            QAEngineerAgent(),
            HRAgent(),
        ]

        # Register each agent
        for agent in agents_to_register:
            agent_type = agent.get_agent_type()
            self._agents[agent_type] = agent
            logger.debug(f"Registered agent: {agent_type}")

        logger.info(f"Agent registry initialized with {len(self._agents)} agents")

    def get(self, agent_type: str) -> Optional[BaseAgent]:
        """
        Get agent by type.

        Args:
            agent_type: Type of agent (e.g., 'marketing', 'frontend_developer')

        Returns:
            Agent instance or None if not found
        """
        agent = self._agents.get(agent_type)

        if not agent:
            logger.warning(f"Agent type '{agent_type}' not found in registry")

        return agent

    def list_agents(self) -> List[str]:
        """
        Get list of all available agent types.

        Returns:
            List of agent type strings
        """
        return list(self._agents.keys())

    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """
        Get all registered agents.

        Returns:
            Dictionary of agent_type -> agent instance
        """
        return self._agents.copy()

    def register_agent(self, agent: BaseAgent):
        """
        Register a new agent dynamically.

        Args:
            agent: Agent instance to register
        """
        agent_type = agent.get_agent_type()
        self._agents[agent_type] = agent
        logger.info(f"Dynamically registered agent: {agent_type}")


# Global registry instance
_registry = AgentRegistry()


# Convenience functions
def get_agent(agent_type: str) -> Optional[BaseAgent]:
    """
    Get agent by type from global registry.

    Args:
        agent_type: Type of agent

    Returns:
        Agent instance or None if not found
    """
    return _registry.get(agent_type)


def list_agents() -> List[str]:
    """
    Get list of all available agent types.

    Returns:
        List of agent type strings
    """
    return _registry.list_agents()


def get_all_agents() -> Dict[str, BaseAgent]:
    """
    Get all registered agents.

    Returns:
        Dictionary of agent_type -> agent instance
    """
    return _registry.get_all_agents()


def register_agent(agent: BaseAgent):
    """
    Register a new agent dynamically.

    Args:
        agent: Agent instance to register
    """
    _registry.register_agent(agent)
