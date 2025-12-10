"""WebSocket Connection Manager

Manages WebSocket connections and message broadcasting.
"""

from typing import Dict, List, Optional
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._connection_count = 0

    async def connect(self, websocket: WebSocket, run_id: str):
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket connection
            run_id: Run identifier to associate with connection
        """
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
        self._connection_count += 1
        logger.info(f"WebSocket connected for run {run_id}. Total connections: {self._connection_count}")

    def disconnect(self, websocket: WebSocket, run_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            run_id: Run identifier
        """
        if run_id in self.active_connections:
            try:
                self.active_connections[run_id].remove(websocket)
                self._connection_count -= 1
                logger.info(f"WebSocket disconnected for run {run_id}. Total connections: {self._connection_count}")
            except ValueError:
                pass  # Already removed

            if not self.active_connections[run_id]:
                del self.active_connections[run_id]

    async def send_message(self, run_id: str, message: dict):
        """
        Send message to all connections for a run_id.

        Args:
            run_id: Run identifier
            message: Message dictionary to send

        Returns:
            Number of successful sends
        """
        if run_id not in self.active_connections:
            return 0

        disconnected = []
        success_count = 0

        for connection in self.active_connections[run_id]:
            try:
                await connection.send_json(message)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, run_id)

        return success_count

    async def broadcast(self, message: dict):
        """
        Broadcast message to all active connections.

        Args:
            message: Message dictionary to broadcast

        Returns:
            Number of successful broadcasts
        """
        total_sent = 0
        for run_id in list(self.active_connections.keys()):
            sent = await self.send_message(run_id, message)
            total_sent += sent
        return total_sent

    def get_connection_count(self, run_id: Optional[str] = None) -> int:
        """
        Get number of active connections.

        Args:
            run_id: Optional run ID to filter by

        Returns:
            Connection count
        """
        if run_id:
            return len(self.active_connections.get(run_id, []))
        return self._connection_count

    def get_active_runs(self) -> List[str]:
        """
        Get list of run IDs with active connections.

        Returns:
            List of run IDs
        """
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
