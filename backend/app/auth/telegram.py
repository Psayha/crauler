import hashlib
import hmac
from typing import Optional, Dict, Any
from urllib.parse import parse_qsl
import logging

logger = logging.getLogger(__name__)


class TelegramAuth:
    """
    Telegram Mini App authentication handler
    Validates initData from Telegram WebApp
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def validate_init_data(self, init_data: str) -> Optional[Dict[str, Any]]:
        """
        Validate Telegram WebApp initData

        Args:
            init_data: Raw initData string from Telegram WebApp

        Returns:
            Parsed and validated data or None if invalid
        """
        try:
            # Parse initData
            parsed_data = dict(parse_qsl(init_data))

            # Extract hash
            received_hash = parsed_data.pop("hash", None)
            if not received_hash:
                logger.warning("No hash found in initData")
                return None

            # Create data-check-string
            data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
            data_check_string = "\n".join(data_check_arr)

            # Compute secret key
            secret_key = hmac.new(
                key=b"WebAppData",
                msg=self.bot_token.encode(),
                digestmod=hashlib.sha256
            ).digest()

            # Compute hash
            computed_hash = hmac.new(
                key=secret_key,
                msg=data_check_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()

            # Verify hash
            if not hmac.compare_digest(computed_hash, received_hash):
                logger.warning("Invalid hash in initData")
                return None

            # Parse user data
            import json
            if "user" in parsed_data:
                parsed_data["user"] = json.loads(parsed_data["user"])

            logger.info(f"Successfully validated initData for user {parsed_data.get('user', {}).get('id')}")
            return parsed_data

        except Exception as e:
            logger.error(f"Error validating initData: {e}")
            return None

    def extract_user_data(self, validated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract user information from validated initData

        Returns:
            User data dictionary or None
        """
        if not validated_data or "user" not in validated_data:
            return None

        user = validated_data["user"]

        return {
            "telegram_id": user.get("id"),
            "username": user.get("username"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "language_code": user.get("language_code", "ru"),
            "is_premium": user.get("is_premium", False),
            "photo_url": user.get("photo_url"),
        }
