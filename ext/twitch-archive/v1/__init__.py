import os
from typing import List
from hashlib import sha256

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, PlainTextResponse

SECRET = os.environ.get("TWITCH_WS_SECRET")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message):
        for connection in self.active_connections:
                await connection.send_json(message)


router = APIRouter(prefix="/v1")
manager = ConnectionManager()

user_ids = []

@router.post('/stream/{user_id}')
async def stream(request: Request, user_id: str):
    signature = request.headers.get("X-Hub-Signature", "").replace("sha256=", "")
    payload = await request.body()

    if signature != sha256(payload + SECRET.encode()).hexdigest():
        return Response(status_code=403)

    data = await request.json()
    await manager.broadcast({
            "type": "stream",
            "user": user_id,
            "payload": data["data"]
        })

    return Response(status_code=202)

# this is how Twitch verifies ownership of the endpoint
@router.get('/stream/{user_id}')
async def stream_verification(request: Request, user_id: str):
    if not user_id or user_id not in user_ids:
        return Response(status_code=403)

    user_ids.remove(user_id)

    challenge = request.query_params["hub.challenge"]
    return PlainTextResponse(challenge, status_code=200)

# websockets don't care about the router heirchy for some reason
@router.websocket("/twitch-archive/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    if SECRET != websocket.headers.get("Authorization").replace("Bearer ", ""): # shitty auth
        return

    print(f'New WS connection: {websocket.client}')
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            _type = data.get("type")
            user_id = data.get("user_id")

            if _type == "stream_add":
                user_ids.append(user_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f'WS client disconnected: {websocket.client}')


def setup(app):
    pass
