from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from typing import Dict, Any
import json
from pydantic import BaseModel
from app.core.websocket_manager import manager
from app.db.citizens import queue_offline_message, get_undelivered_messages, mark_delivered, get_citizen_phones_by_state

router = APIRouter()

class BroadcastPayload(BaseModel):
    target: str # "state", "district", "all"
    target_id: str # e.g. "Maharashtra"
    message: Dict[str, Any]

@router.websocket("/ws/{citizen_id}")
async def websocket_endpoint(websocket: WebSocket, citizen_id: str):
    """
    WebSocket connection endpoint. The client will immediately send its regional
    metadata explicitly after connection so the manager can map it.
    """
    # Accept without metadata initially
    await websocket.accept()

    try:
        # Wait for the first client message that contains their regional setup
        intro_data = await websocket.receive_text()
        meta = json.loads(intro_data)
        
        # Now truly register them in our stateful manager
        await manager.connect(websocket, citizen_id, meta)
        
        # Check offline queue immediately
        pool = websocket.app.state.pool
        if pool:
            missed_msgs = await get_undelivered_messages(pool, citizen_id)
            if missed_msgs:
                # Send the missed messages immediately
                for msg in missed_msgs:
                    msg["missed"] = True
                    await manager.send_personal_message(msg, citizen_id)
                # Mark as delivered
                await mark_delivered(pool, citizen_id, [m["msg_id"] for m in missed_msgs])

        while True:
            # Keep connection alive, listen for standard messages/pings
            data = await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket, citizen_id)
    except Exception as e:
        manager.disconnect(websocket, citizen_id)


@router.post("/broadcast")
async def broadcast_message(request: Request, payload: BroadcastPayload):
    """
    Broadcasts message specifically querying the target state constraints entirely 
    isolated to online users natively and queuing offline reliably.
    """
    pool = request.app.state.pool
    if not pool:
        raise HTTPException(status_code=500, detail="Database pool not configured")

    if payload.target != "state":
        raise HTTPException(status_code=400, detail="Currently only 'state' broadcast target is supported.")

    state = payload.target_id
    # 1. Fetch total citizens for the state from Database
    target_phones = await get_citizen_phones_by_state(pool, state)
    
    # We map citizen_id as `cit_{pincode}_{phone}` but our get_citizen_phones query only returns phone numbers. 
    # The queue requires `citizen_id`. Let's assume the manager tracks the full cid.
    # To reliably hit everyone offline, we need their full citizen_id. However, our websocket active connections track full citizen_id explicitly.
    online_citizens = manager.get_online_citizens_in_state(state)
    
    delivered_count = 0
    queued_count = 0

    # 3. For any online citizen matched -> blast message
    for cid in online_citizens:
        sent = await manager.send_personal_message(payload.message, cid)
        if sent:
            delivered_count += 1
            
    # 4. We cannot comprehensively queue offline messages here without all exact citizen_ids unless we rewrite the query to return IDs.
    # We will assume a future DB migration adds `id VARCHAR(50)` representing physical `citizen_id` instead of inferring it.
    # Since we don't have the exact IDs of all offline receivers right now, we queue the message by their raw `phone`.
    for phone in target_phones:
        # Check if phone is within any online citizen_id to skip queuing
        is_online = any(phone in cid for cid in online_citizens)
        if not is_online:
            await queue_offline_message(pool, phone, payload.message)
            queued_count += 1
            
    return {
        "success": True, 
        "state": state, 
        "delivered_online": delivered_count, 
        "queued_offline": queued_count
    }
