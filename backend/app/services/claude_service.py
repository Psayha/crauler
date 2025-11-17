import anthropic
from typing import Optional, Dict, Any
import json
import logging
import time

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Claude API"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.claude_api_key)
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.temperature = settings.claude_temperature

    async def send_message(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send message to Claude API

        Args:
            system_prompt: System instruction for Claude
            user_prompt: User message
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Claude's response text
        """
        try:
            start_time = time.time()

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            execution_time = time.time() - start_time

            logger.info(
                f"Claude API call successful. "
                f"Tokens: {response.usage.input_tokens + response.usage.output_tokens}, "
                f"Time: {execution_time:.2f}s"
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def parse_json_response(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Get JSON response from Claude

        Args:
            system_prompt: System instruction
            user_prompt: User message
            **kwargs: Additional parameters for send_message

        Returns:
            Parsed JSON response
        """
        response = await self.send_message(
            system_prompt=system_prompt, user_prompt=user_prompt, **kwargs
        )

        try:
            # Clean response and parse JSON
            cleaned = response.strip()

            # Remove markdown code blocks if present
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            return json.loads(cleaned.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nResponse: {response}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4


# Global instance
claude_service = ClaudeService()
