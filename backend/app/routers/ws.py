from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from fastapi import HTTPException

from app.security import optional_decode_access_token


router = APIRouter(prefix="/ws", tags=["ws"])


@router.websocket("/alerts")
async def alerts_socket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    try:
        payload = optional_decode_access_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return
    organisation_id = None
    if payload is not None:
        organisation_id = payload.get("org_id")
        if organisation_id is not None and not isinstance(organisation_id, str):
            await websocket.close(code=1008)
            return

    notifier = websocket.app.state.notifier
    await notifier.connect(websocket, organisation_id=organisation_id)
    try:
        for message in notifier.recent_messages():
            message_org_id = message.get("organisation_id")
            if organisation_id is None or message_org_id in (None, organisation_id):
                await websocket.send_json(message)

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notifier.disconnect(websocket)
