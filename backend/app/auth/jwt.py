from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Load from config
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Payload data to encode
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT access token

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def create_user_token(user_id: str, telegram_id: int) -> str:
    """
    Create access token for user

    Args:
        user_id: User UUID
        telegram_id: Telegram user ID

    Returns:
        JWT token
    """
    payload = {
        "sub": user_id,
        "telegram_id": telegram_id,
        "type": "access"
    }

    return create_access_token(payload)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload

    Args:
        token: JWT token string

    Returns:
        Token payload or None if invalid
    """
    payload = decode_access_token(token)

    if payload is None:
        return None

    # Check if token has expired
    exp = payload.get("exp")
    if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
        logger.warning("Token has expired")
        return None

    return payload
