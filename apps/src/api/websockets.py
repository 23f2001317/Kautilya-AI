# apps/src/api/websockets.py
"""Real-time WebSocket event broadcaster for dashboard telemetry and agent logs."""

import json
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["WebSockets"])


class IncidentConnectionManager:
    """Manages active WebSocket subscriber connections for real-time state sync."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register an active WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("ws_client_connected", total_clients=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("ws_client_disconnected", total_clients=len(self.active_connections))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast a structured JSON event to all connected dashboard clients."""
        payload = json.dumps({"event": event_type, "data": data})
        stale_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as exc:
                logger.warning("ws_send_failed", error=str(exc))
                stale_connections.append(connection)

        for stale in stale_connections:
            self.disconnect(stale)


ws_manager = IncidentConnectionManager()


@router.websocket("/ws/incidents")
async def incident_websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint streaming incident changes, agent logs, and topology updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Maintain persistent connection and handle client ping/ack
            data = await websocket.receive_text()
            logger.debug("ws_client_message_received", data=data)
            await websocket.send_text(json.dumps({"event": "ack", "received": data}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
