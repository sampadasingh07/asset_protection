from collections import deque
from dataclasses import dataclass

from fastapi import WebSocket


@dataclass
class _Connection:
    websocket: WebSocket
    organisation_id: str | None


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[_Connection] = []
        self._history: deque[dict[str, object]] = deque(maxlen=25)

    async def connect(self, websocket: WebSocket, organisation_id: str | None = None) -> None:
        await websocket.accept()
        self._connections.append(_Connection(websocket=websocket, organisation_id=organisation_id))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections = [
            connection
            for connection in self._connections
            if connection.websocket is not websocket
        ]

    async def broadcast(
        self,
        payload: dict[str, object],
        *,
        organisation_id: str | None = None,
    ) -> None:
        self._history.append(payload)
        stale_connections: list[WebSocket] = []

        for connection in list(self._connections):
            if organisation_id and connection.organisation_id not in (None, organisation_id):
                continue
            try:
                await connection.websocket.send_json(payload)
            except Exception:
                stale_connections.append(connection.websocket)

        for websocket in stale_connections:
            self.disconnect(websocket)

    def recent_messages(self) -> list[dict[str, object]]:
        return list(self._history)
