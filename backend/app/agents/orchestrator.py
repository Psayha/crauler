import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
from uuid import uuid4

from app.services.claude_service import claude_service
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.database.connection import get_db
from sqlalchemy import select
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Main orchestrator for AI Agency
    Acts as CEO/Product Manager coordinating all agents
    """

    def get_agent_type(self) -> str:
        """Return agent type identifier"""
        return "orchestrator"

    def get_temperature(self) -> float:
        """Return temperature for Claude API calls"""
        return 0.5

    def get_system_prompt(self) -> str:
        """Return system prompt for orchestrator"""
        return """You are the CEO and Chief Orchestrator of an AI Agency.

Your role is to:
1. Analyze incoming project requests and understand their full scope
2. Decompose projects into specific, actionable tasks
3. Assign tasks to the most suitable specialist agents
4. Monitor progress and ensure quality standards
5. Integrate results into cohesive deliverables
6. Maintain communication with stakeholders

You have the following specialist agents at your disposal:
- marketing: Marketing strategies, content planning, SEO/SEM
- frontend_developer: React, Next.js, UI/UX implementation
- backend_developer: APIs, databases, business logic
- mobile_developer: iOS/Android applications
- devops: Infrastructure, deployment, CI/CD
- data_analyst: Data analysis, reporting, insights
- ux_designer: User research, wireframes, prototypes
- project_manager: Sprint planning, task tracking
- qa_engineer: Testing, quality assurance
- content_writer: Blog posts, documentation, copy

Decision Framework:
- Prioritize tasks by impact and dependencies
- Optimize for parallel execution where possible
- Ensure quality gates at each stage
- Balance speed with thoroughness
- Consider token budget constraints

Output Format:
Always structure your responses as JSON with clear action items and rationale."""

    async def analyze_project(
        self, request: str, organization_id: str
    ) -> Dict[str, Any]:
        """
        Analyze incoming project request

        Args:
            request: Project description from client
            organization_id: Organization ID

        Returns:
            Project analysis with metadata
        """
        analysis_prompt = f"""Analyze this project request and provide a structured breakdown:

Request: {request}

Provide a JSON response with:
1. project_name: Suggested project name (max 100 chars)
2. project_type: One of [website, mobile_app, marketing_campaign, data_analysis, content_creation, custom]
3. complexity: One of [simple, moderate, complex, enterprise]
4. estimated_hours: Number (realistic estimation)
5. required_agents: List of agent types needed (from available list)
6. key_requirements: List of main requirements (3-7 items)
7. potential_risks: List of risks (2-5 items)
8. success_criteria: List of measurable outcomes (3-5 items)
9. recommended_approach: Brief strategy (2-3 sentences)

Be specific and realistic in your analysis."""

        try:
            response = await claude_service.parse_json_response(
                system_prompt=self.system_prompt,
                user_prompt=analysis_prompt,
                temperature=0.3,
            )

            # Validate project_type
            valid_types = [t.value for t in ProjectType]
            if response.get("project_type") not in valid_types:
                response["project_type"] = "custom"

            return response

        except Exception as e:
            logger.error(f"Project analysis failed: {e}")
            raise

    async def decompose_project(
        self, project: Project
    ) -> List[Dict[str, Any]]:
        """
        Decompose project into tasks

        Args:
            project: Project object

        Returns:
            List of task definitions
        """
        decomposition_prompt = f"""Decompose this project into specific tasks:

Project Name: {project.name}
Project Type: {project.type.value}
Description: {project.description}
Requirements: {json.dumps(project.metadata.get('key_requirements', []), indent=2)}
Estimated Hours: {project.metadata.get('estimated_hours', 'unknown')}

Create a detailed task breakdown with:
{{
  "tasks": [
    {{
      "title": "Clear task title",
      "description": "Detailed description of what needs to be done",
      "agent_type": "Which agent from available list",
      "dependencies": [0, 1],  // indices of tasks this depends on (empty array if none)
      "estimated_tokens": 1000,  // realistic token estimate
      "deliverables": ["Expected output 1", "Expected output 2"],
      "acceptance_criteria": ["How to verify completion"]
    }}
  ],
  "execution_order": [0, 1, 2, 3],  // optimal sequence
  "parallel_groups": [[0, 1], [2, 3]],  // tasks that can run together
  "critical_path": [0, 2, 4]  // tasks that directly impact timeline
}}

Guidelines:
- Create 3-10 tasks depending on project complexity
- Each task should be specific and assignable to ONE agent
- Consider dependencies carefully
- Tasks should be completable independently
- Estimate tokens realistically (500-3000 per task)"""

        try:
            response = await claude_service.parse_json_response(
                system_prompt=self.system_prompt,
                user_prompt=decomposition_prompt,
                temperature=0.2,
            )

            return response.get("tasks", [])

        except Exception as e:
            logger.error(f"Project decomposition failed: {e}")
            raise

    async def create_project(
        self, request: str, organization_id: str
    ) -> Project:
        """
        Create new project from request

        Args:
            request: Project description
            organization_id: Organization ID

        Returns:
            Created project
        """
        # Analyze request
        analysis = await self.analyze_project(request, organization_id)

        # Create project in database
        async with get_db() as db:
            project = Project(
                id=uuid4(),
                organization_id=organization_id,
                name=analysis["project_name"],
                description=request,
                type=ProjectType(analysis["project_type"]),
                status=ProjectStatus.PLANNING,
                priority=self._determine_priority(analysis),
                deadline=self._calculate_deadline(
                    analysis.get("estimated_hours", 40)
                ),
                metadata=analysis,
            )

            db.add(project)
            await db.commit()
            await db.refresh(project)

            logger.info(f"Created project: {project.id} - {project.name}")

            # Decompose into tasks
            task_definitions = await self.decompose_project(project)

            # Create tasks in database
            for idx, task_def in enumerate(task_definitions):
                task = Task(
                    id=uuid4(),
                    project_id=project.id,
                    title=task_def["title"],
                    description=task_def["description"],
                    assigned_agent=task_def["agent_type"],
                    status=TaskStatus.PENDING,
                    priority=self._calculate_task_priority(task_def, analysis),
                    input_data={
                        "deliverables": task_def.get("deliverables", []),
                        "acceptance_criteria": task_def.get(
                            "acceptance_criteria", []
                        ),
                        "project_context": analysis,
                    },
                    estimated_tokens=task_def.get("estimated_tokens", 1000),
                )

                db.add(task)

            await db.commit()

            logger.info(
                f"Created {len(task_definitions)} tasks for project {project.id}"
            )

            return project

    def _determine_priority(self, analysis: Dict[str, Any]) -> str:
        """Determine project priority from analysis"""
        complexity = analysis.get("complexity", "moderate")

        if complexity == "enterprise":
            return "high"
        elif complexity == "complex":
            return "normal"
        else:
            return "normal"

    def _calculate_deadline(self, estimated_hours: int) -> datetime:
        """Calculate project deadline"""
        # Add 50% buffer
        hours_with_buffer = int(estimated_hours * 1.5)
        return datetime.utcnow() + timedelta(hours=hours_with_buffer)

    def _calculate_task_priority(
        self, task_def: Dict[str, Any], analysis: Dict[str, Any]
    ) -> TaskPriority:
        """Calculate task priority"""
        # Tasks with no dependencies are higher priority
        if not task_def.get("dependencies"):
            return TaskPriority.HIGH

        return TaskPriority.NORMAL


# Export alias for backwards compatibility with tests
Orchestrator = OrchestratorAgent

# Global instance
orchestrator = OrchestratorAgent()
