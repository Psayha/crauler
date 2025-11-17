"""
HR Agent - Meta-agent for managing and improving the agent team.

Responsibilities:
1. Agent Upskilling - Analyze and improve agent performance
2. Agent Recruitment - Create new specialized agents dynamically
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from .base_agent import BaseAgent


class HRAgent(BaseAgent):
    """
    HR Agent (Human Resources Manager)

    A meta-agent that manages the agent team by:
    - Analyzing agent performance metrics
    - Suggesting improvements to agent configurations
    - Testing agent variants
    - Creating new specialized agents when needed
    """

    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "hr_manager"

    def get_temperature(self) -> float:
        """
        Return the temperature for this agent.
        Balanced temperature for analytical and creative work.
        """
        return 0.4

    def get_system_prompt(self) -> str:
        """Return the system prompt for HR Agent."""
        return """You are an HR Manager for an AI agent team. Your role is to:

1. ANALYZE AGENT PERFORMANCE:
   - Review metrics: success rate, execution time, token efficiency
   - Identify patterns in successes and failures
   - Compare agent performance across different task types
   - Spot opportunities for improvement

2. SUGGEST IMPROVEMENTS:
   - Optimize system prompts for better results
   - Recommend temperature adjustments
   - Propose A/B tests for configurations
   - Suggest training data or examples

3. CREATE NEW AGENTS:
   - Identify skill gaps in the team
   - Design new specialized agents
   - Define agent expertise and capabilities
   - Generate system prompts for new agents

4. VALIDATE CHANGES:
   - Test improvements before deployment
   - Measure performance impact
   - Ensure quality standards
   - Recommend rollout strategy

Be analytical, data-driven, and focused on continuous improvement. Provide specific, actionable recommendations with clear reasoning."""

    async def analyze_agent_performance(
        self,
        agent_type: str,
        metrics: Dict[str, Any],
        time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Analyze performance of a specific agent.

        Args:
            agent_type: Type of agent to analyze
            metrics: Performance metrics data
            time_period: Time period for analysis

        Returns:
            Analysis report with insights and recommendations
        """
        prompt = f"""Analyze the performance of the {agent_type} agent over the last {time_period}.

Performance Metrics:
{json.dumps(metrics, indent=2)}

Provide:
1. Overall performance assessment
2. Key strengths
3. Areas for improvement
4. Specific actionable recommendations
5. Priority level for improvements (critical/high/medium/low)

Format your response as JSON with these fields:
{{
    "overall_score": <0-100>,
    "assessment": "<summary>",
    "strengths": ["<strength1>", "<strength2>"],
    "weaknesses": ["<weakness1>", "<weakness2>"],
    "recommendations": [
        {{
            "type": "<prompt_update/temperature_change/etc>",
            "description": "<what to change>",
            "expected_impact": "<high/medium/low>",
            "priority": "<critical/high/medium/low>"
        }}
    ],
    "next_steps": ["<step1>", "<step2>"]
}}"""

        response = await self.execute(prompt)

        try:
            # Clean response if it contains markdown code blocks
            cleaned_response = self.clean_json_response(response)
            analysis = json.loads(cleaned_response)
            return analysis
        except json.JSONDecodeError:
            # Fallback to structured response
            return {
                "overall_score": 70,
                "assessment": response[:500],
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "next_steps": [],
                "raw_response": response
            }

    async def suggest_improvements(
        self,
        agent_type: str,
        current_config: Dict[str, Any],
        performance_issues: List[str]
    ) -> Dict[str, Any]:
        """
        Suggest improvements for an agent based on performance issues.

        Args:
            agent_type: Type of agent
            current_config: Current agent configuration
            performance_issues: List of identified issues

        Returns:
            Improvement suggestions
        """
        prompt = f"""Suggest improvements for the {agent_type} agent.

Current Configuration:
{json.dumps(current_config, indent=2)}

Performance Issues:
{json.dumps(performance_issues, indent=2)}

Suggest specific improvements to:
1. System prompt
2. Temperature settings
3. Max tokens
4. Response format
5. Any other relevant parameters

Provide detailed, actionable suggestions with reasoning.

Format as JSON:
{{
    "improvements": [
        {{
            "type": "<improvement_type>",
            "current_value": "<current>",
            "proposed_value": "<proposed>",
            "reasoning": "<why this will help>",
            "expected_impact": "<high/medium/low>",
            "test_plan": "<how to test this>"
        }}
    ],
    "priority_order": ["<improvement1>", "<improvement2>"],
    "estimated_improvement": "<percentage>"
}}"""

        response = await self.execute(prompt)

        try:
            cleaned_response = self.clean_json_response(response)
            suggestions = json.loads(cleaned_response)
            return suggestions
        except json.JSONDecodeError:
            return {
                "improvements": [],
                "priority_order": [],
                "estimated_improvement": "unknown",
                "raw_response": response
            }

    async def identify_skill_gaps(
        self,
        project_description: str,
        current_agents: List[str],
        task_breakdown: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify skill gaps in the current agent team for a project.

        Args:
            project_description: Project description
            current_agents: List of available agent types
            task_breakdown: Breakdown of project tasks

        Returns:
            Skill gap analysis
        """
        prompt = f"""Analyze this project to identify skill gaps in our agent team.

Project: {project_description}

Current Agents:
{json.dumps(current_agents, indent=2)}

Task Breakdown:
{json.dumps(task_breakdown, indent=2)}

Identify:
1. Tasks that don't match any current agent's expertise
2. Specialized skills needed but not available
3. Recommended new agent types to add

Format as JSON:
{{
    "skill_gaps": [
        {{
            "skill": "<missing skill>",
            "importance": "<critical/high/medium/low>",
            "affected_tasks": ["<task1>", "<task2>"],
            "workaround": "<current workaround if any>"
        }}
    ],
    "recommended_agents": [
        {{
            "agent_type": "<new_agent_type>",
            "name": "<agent name>",
            "primary_skills": ["<skill1>", "<skill2>"],
            "justification": "<why needed>"
        }}
    ]
}}"""

        response = await self.execute(prompt)

        try:
            cleaned_response = self.clean_json_response(response)
            analysis = json.loads(cleaned_response)
            return analysis
        except json.JSONDecodeError:
            return {
                "skill_gaps": [],
                "recommended_agents": [],
                "raw_response": response
            }

    async def design_new_agent(
        self,
        agent_type: str,
        required_skills: List[str],
        project_context: str
    ) -> Dict[str, Any]:
        """
        Design a new specialized agent.

        Args:
            agent_type: Proposed agent type identifier
            required_skills: Required skills and expertise
            project_context: Context about why this agent is needed

        Returns:
            Complete agent specification
        """
        prompt = f"""Design a new AI agent with the following specifications:

Agent Type: {agent_type}
Required Skills: {json.dumps(required_skills, indent=2)}
Context: {project_context}

Create a complete agent specification including:
1. Agent name and description
2. Detailed system prompt
3. Recommended temperature (0.0-1.0)
4. Expertise areas
5. Example tasks this agent should handle
6. Key performance indicators

Format as JSON:
{{
    "agent_type": "<identifier>",
    "name": "<human-readable name>",
    "description": "<detailed description>",
    "system_prompt": "<complete system prompt>",
    "temperature": <0.0-1.0>,
    "max_tokens": <recommended>,
    "expertise": ["<skill1>", "<skill2>"],
    "example_tasks": ["<task1>", "<task2>"],
    "kpis": ["<kpi1>", "<kpi2>"],
    "capabilities": {{
        "<capability>": "<description>"
    }}
}}"""

        response = await self.execute(prompt)

        try:
            cleaned_response = self.clean_json_response(response)
            agent_spec = json.loads(cleaned_response)
            return agent_spec
        except json.JSONDecodeError:
            return {
                "agent_type": agent_type,
                "name": agent_type.replace("_", " ").title(),
                "error": "Failed to parse agent specification",
                "raw_response": response
            }

    def clean_json_response(self, response: str) -> str:
        """
        Clean JSON response by removing markdown code blocks.

        Args:
            response: Raw response string

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        return response.strip()
