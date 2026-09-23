"""WebSocket endpoint: push real-time P&L, CRT scan updates, Photon expectations, alerts."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

_connections: list[WebSocket] = []


async def ws_endpoint(websocket: WebSocket):
    """Main WebSocket handler — clients connect here for real-time updates."""
    await websocket.accept()
    _connections.append(websocket)
    logger.info("WebSocket client connected (%d total)", len(_connections))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections.remove(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(_connections))


async def broadcast(event_type: str, data: dict[str, Any]) -> None:
    """Broadcast an event to all connected WebSocket clients."""
    message = json.dumps({"type": event_type, "data": data})
    dead = []
    for ws in _connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections.remove(ws)


def broadcast_sync(event_type: str, data: dict[str, Any]) -> None:
    """Synchronous wrapper for broadcasting from non-async code."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast(event_type, data))
        else:
            loop.run_until_complete(broadcast(event_type, data))
    except RuntimeError:
        pass
