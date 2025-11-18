from typing import Dict, Set
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager
    Manages real-time connections for project and task updates
    """

    def __init__(self):
        # User connections: {user_id: {websocket1, websocket2, ...}}
        self.user_connections: Dict[str, Set[WebSocket]] = {}

        # Project connections: {project_id: {websocket1, websocket2, ...}}
        self.project_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Add new WebSocket connection for user

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()

        self.user_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.user_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove WebSocket connection

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)

            # Remove user entry if no connections left
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected")

    async def subscribe_to_project(self, websocket: WebSocket, project_id: str):
        """
        Subscribe WebSocket to project updates

        Args:
            websocket: WebSocket connection
            project_id: Project ID
        """
        if project_id not in self.project_connections:
            self.project_connections[project_id] = set()

        self.project_connections[project_id].add(websocket)
        logger.info(f"Subscribed to project {project_id}. Total subscribers: {len(self.project_connections[project_id])}")

    def unsubscribe_from_project(self, websocket: WebSocket, project_id: str):
        """
        Unsubscribe WebSocket from project updates

        Args:
            websocket: WebSocket connection
            project_id: Project ID
        """
        if project_id in self.project_connections:
            self.project_connections[project_id].discard(websocket)

            # Remove project entry if no connections left
            if not self.project_connections[project_id]:
                del self.project_connections[project_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to specific WebSocket

        Args:
            message: Message data
            websocket: WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast_to_user(self, message: dict, user_id: str):
        """
        Broadcast message to all user's connections

        Args:
            message: Message data
            user_id: User ID
        """
        if user_id not in self.user_connections:
            return

        disconnected = set()

        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            self.user_connections[user_id].discard(websocket)

    async def broadcast_to_project(self, message: dict, project_id: str):
        """
        Broadcast message to all project subscribers

        Args:
            message: Message data
            project_id: Project ID
        """
        if project_id not in self.project_connections:
            return

        disconnected = set()

        for websocket in self.project_connections[project_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to project {project_id}: {e}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            self.project_connections[project_id].discard(websocket)

    async def notify_project_update(self, project_id: str, update_type: str, data: dict):
        """
        Send project update notification

        Args:
            project_id: Project ID
            update_type: Type of update (status_changed, task_completed, etc.)
            data: Update data
        """
        message = {
            "type": "project_update",
            "project_id": project_id,
            "update_type": update_type,
            "data": data,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }

        await self.broadcast_to_project(message, project_id)
        logger.info(f"Notified project {project_id}: {update_type}")

    async def notify_task_update(self, project_id: str, task_id: str, status: str, data: dict = None):
        """
        Send task update notification

        Args:
            project_id: Project ID
            task_id: Task ID
            status: Task status
            data: Additional task data
        """
        message = {
            "type": "task_update",
            "project_id": project_id,
            "task_id": task_id,
            "status": status,
            "data": data or {},
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }

        await self.broadcast_to_project(message, project_id)
        logger.info(f"Notified task {task_id} update: {status}")

    async def notify_agent_activity(self, project_id: str, agent_type: str, activity: str, task_id: str = None):
        """
        Send agent activity notification

        Args:
            project_id: Project ID
            agent_type: Type of agent
            activity: Activity description
            task_id: Related task ID
        """
        message = {
            "type": "agent_activity",
            "project_id": project_id,
            "agent_type": agent_type,
            "activity": activity,
            "task_id": task_id,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }

        await self.broadcast_to_project(message, project_id)
        logger.debug(f"Notified agent activity: {agent_type} - {activity}")


# Global connection manager instance
connection_manager = ConnectionManager()

# Alias for backward compatibility
ws_manager = connection_manager
