from fastapi import APIRouter
from typing import List, Dict, Any
import logging

from app.agents.base_agent import agent_registry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_agents() -> Dict[str, Any]:
    """
    List all available AI agents

    Returns information about registered agents in the system
    """
    agents = agent_registry.list_agents()

    # Build agent info
    agent_info = []

    for agent_type in agents:
        agent = agent_registry.get_agent(agent_type)

        # Determine agent role/description
        role_map = {
            "marketing": "Chief Marketing Officer - Marketing strategies & growth",
            "frontend_developer": "Senior Frontend Developer - React/Next.js expert",
            "backend_developer": "Senior Backend Developer - API & system architecture",
            "data_analyst": "Senior Data Analyst - Data analysis & BI",
            "ux_designer": "Senior UX/UI Designer - User experience & design",
            "content_writer": "Senior Content Writer - SEO & copywriting",
        }

        agent_info.append(
            {
                "agent_type": agent_type,
                "role": role_map.get(agent_type, "Specialized Agent"),
                "temperature": agent.temperature,
            }
        )

    return {
        "total_agents": len(agents),
        "agents": agent_info,
    }


@router.get("/{agent_type}")
async def get_agent_info(agent_type: str) -> Dict[str, Any]:
    """
    Get information about a specific agent

    Args:
        agent_type: Type of agent to get info for
    """
    agent = agent_registry.get_agent(agent_type)

    if not agent:
        return {"error": f"Agent type '{agent_type}' not found"}

    # Extract first few lines of system prompt as description
    system_prompt = agent.system_prompt
    description_lines = system_prompt.split("\n")[:3]
    description = " ".join(description_lines)

    return {
        "agent_type": agent_type,
        "description": description,
        "temperature": agent.temperature,
        "available": True,
    }
