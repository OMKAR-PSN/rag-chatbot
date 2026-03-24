from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Maps citizen_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Maps websocket -> Dictionary of state metadata
        self.connection_metadata: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, citizen_id: str, meta: dict):
        await websocket.accept()
        self.active_connections[citizen_id] = websocket
        self.connection_metadata[websocket] = meta

    def disconnect(self, websocket: WebSocket, citizen_id: str):
        if citizen_id in self.active_connections:
            del self.active_connections[citizen_id]
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

    async def send_personal_message(self, message: dict, citizen_id: str) -> bool:
        if citizen_id in self.active_connections:
            websocket = self.active_connections[citizen_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception:
                self.disconnect(websocket, citizen_id)
                return False
        return False

    def get_online_citizens_in_state(self, state: str) -> list[str]:
        # Returns list of citizen_ids online in that state
        online = []
        for ws, meta in self.connection_metadata.items():
            if meta.get("state") == state:
                # Find citizen_id for this websocket
                for cid, w in self.active_connections.items():
                    if w == ws:
                        online.append(cid)
                        break
        return online

manager = ConnectionManager()
