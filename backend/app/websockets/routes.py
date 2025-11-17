from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.websockets.manager import connection_manager
from app.auth.jwt import verify_token
from app.database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates

    Args:
        websocket: WebSocket connection
        token: JWT access token (from query params)
        db: Database session

    Usage:
        ws://localhost:8000/ws?token=your_jwt_token
    """
    # Verify token
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    # Connect user
    await connection_manager.connect(websocket, user_id)

    try:
        # Send initial connection message
        await connection_manager.send_personal_message(
            {
                "type": "connected",
                "message": "WebSocket connection established",
                "user_id": user_id
            },
            websocket
        )

        # Listen for messages
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "subscribe_project":
                project_id = data.get("project_id")
                if project_id:
                    await connection_manager.subscribe_to_project(websocket, project_id)
                    await connection_manager.send_personal_message(
                        {
                            "type": "subscribed",
                            "project_id": project_id,
                            "message": f"Subscribed to project {project_id}"
                        },
                        websocket
                    )

            elif message_type == "unsubscribe_project":
                project_id = data.get("project_id")
                if project_id:
                    connection_manager.unsubscribe_from_project(websocket, project_id)
                    await connection_manager.send_personal_message(
                        {
                            "type": "unsubscribed",
                            "project_id": project_id,
                            "message": f"Unsubscribed from project {project_id}"
                        },
                        websocket
                    )

            elif message_type == "ping":
                # Respond to ping with pong
                await connection_manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
                    },
                    websocket
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        connection_manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        connection_manager.disconnect(websocket, user_id)
