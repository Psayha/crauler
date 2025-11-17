from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.database.connection import get_db
from app.auth.telegram import TelegramAuth
from app.auth.jwt import create_user_token
from app.auth.dependencies import get_current_user
from app.models.user import User, UserSettings
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class TelegramAuthRequest(BaseModel):
    """Request model for Telegram authentication"""
    init_data: str


class AuthResponse(BaseModel):
    """Response model for authentication"""
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/telegram", response_model=AuthResponse)
async def authenticate_telegram(
    auth_request: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user via Telegram Mini App initData

    Args:
        auth_request: Contains initData from Telegram WebApp
        db: Database session

    Returns:
        JWT access token and user information
    """
    # Initialize Telegram auth handler
    telegram_auth = TelegramAuth(settings.telegram_bot_token)

    # Validate initData
    validated_data = telegram_auth.validate_init_data(auth_request.init_data)
    if not validated_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )

    # Extract user data
    user_data = telegram_auth.extract_user_data(validated_data)
    if not user_data or not user_data.get("telegram_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract user data from Telegram"
        )

    telegram_id = user_data["telegram_id"]

    # Check if user exists
    result = await db.execute(
        select(User).filter(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    # Create new user if doesn't exist
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            language_code=user_data.get("language_code", "ru"),
            is_premium=user_data.get("is_premium", False),
            photo_url=user_data.get("photo_url"),
        )
        db.add(user)
        await db.flush()

        # Create user settings
        user_settings = UserSettings(
            user_id=user.id,
            language=user_data.get("language_code", "ru")
        )
        db.add(user_settings)

        await db.commit()
        await db.refresh(user)

        logger.info(f"Created new user: {user.telegram_id} (@{user.username})")
    else:
        # Update user information
        user.username = user_data.get("username") or user.username
        user.first_name = user_data.get("first_name") or user.first_name
        user.last_name = user_data.get("last_name") or user.last_name
        user.language_code = user_data.get("language_code") or user.language_code
        user.is_premium = user_data.get("is_premium", False)
        user.photo_url = user_data.get("photo_url") or user.photo_url

        from datetime import datetime
        user.last_active_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        logger.info(f"User logged in: {user.telegram_id} (@{user.username})")

    # Generate JWT token
    access_token = create_user_token(str(user.id), user.telegram_id)

    return AuthResponse(
        access_token=access_token,
        user=user.to_dict()
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information

    Args:
        current_user: Current user from JWT token

    Returns:
        User information
    """
    return current_user.to_dict()


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user

    Note: Since we're using stateless JWT, this just returns success.
    Client should delete the token.

    Args:
        current_user: Current user from JWT token

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.telegram_id} (@{current_user.username})")

    return {
        "message": "Successfully logged out",
        "user_id": str(current_user.id)
    }
