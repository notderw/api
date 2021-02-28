from asyncio import sleep
from typing import List

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response


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
                connection.send_json(message)


router = APIRouter(prefix="/v1")
manager = ConnectionManager()

@router.post('/stream')
async def stream(request: Request):
    data = await request.json()
    await manager.broadcast(data)
    return Response(status_code=202)


# websockets don't care about the router heirchy for some reason
@router.websocket("/twitch-archive/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(f'New WS connection: {websocket.client}')
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f'WS client disconnected: {websocket.client}')


def setup(app):
    pass
