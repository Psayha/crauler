from fastapi import APIRouter
from typing import List, Dict, Any
import logging

from app.agents.base_agent import agent_registry

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
async def list_agents() -> List[Dict[str, Any]]:
    """
    List all available AI agents

    Returns information about registered agents in the system
    """
    agents = agent_registry.list_agents()

    # Build agent info
    agent_info = []

    for agent_type in agents:
        agent = agent_registry.get_agent(agent_type)

        # Determine agent name/description
        name_map = {
            "marketing": "Chief Marketing Officer",
            "frontend_developer": "Senior Frontend Developer",
            "backend_developer": "Senior Backend Developer",
            "data_analyst": "Senior Data Analyst",
            "ux_designer": "Senior UX/UI Designer",
            "content_writer": "Senior Content Writer",
            "mobile_developer": "Senior Mobile Developer",
            "devops_engineer": "Senior DevOps Engineer",
            "project_manager": "Senior Project Manager",
            "qa_engineer": "Senior QA Engineer",
            "hr_manager": "HR Manager",
            "orchestrator": "AI Agency Orchestrator",
        }

        description_map = {
            "marketing": "Marketing strategies & growth",
            "frontend_developer": "React/Next.js expert",
            "backend_developer": "API & system architecture",
            "data_analyst": "Data analysis & BI",
            "ux_designer": "User experience & design",
            "content_writer": "SEO & copywriting",
            "mobile_developer": "iOS/Android/Cross-platform",
            "devops_engineer": "Infrastructure & CI/CD",
            "project_manager": "Planning & coordination",
            "qa_engineer": "Testing & quality assurance",
            "hr_manager": "Agent performance & optimization",
            "orchestrator": "Project coordination & task delegation",
        }

        agent_info.append(
            {
                "type": agent_type,
                "name": name_map.get(agent_type, "Specialized Agent"),
                "description": description_map.get(agent_type, "AI specialist"),
                "temperature": agent.temperature,
            }
        )

    return agent_info


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

    # Agent names and descriptions
    name_map = {
        "marketing": "Chief Marketing Officer",
        "frontend_developer": "Senior Frontend Developer",
        "backend_developer": "Senior Backend Developer",
        "data_analyst": "Senior Data Analyst",
        "ux_designer": "Senior UX/UI Designer",
        "content_writer": "Senior Content Writer",
        "mobile_developer": "Senior Mobile Developer",
        "devops_engineer": "Senior DevOps Engineer",
        "project_manager": "Senior Project Manager",
        "qa_engineer": "Senior QA Engineer",
        "hr_manager": "HR Manager",
        "orchestrator": "AI Agency Orchestrator",
    }

    # Extract first few lines of system prompt as expertise
    system_prompt = agent.system_prompt
    expertise_lines = [line.strip() for line in system_prompt.split("\n") if line.strip()][:5]
    expertise = expertise_lines

    return {
        "type": agent_type,
        "name": name_map.get(agent_type, "Specialized Agent"),
        "description": f"{name_map.get(agent_type, 'Agent')} specializing in {agent_type.replace('_', ' ')}",
        "expertise": expertise,
        "temperature": agent.temperature,
        "available": True,
    }
