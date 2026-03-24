from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict

from app.utils.pincode_validator import validate_pincode
from app.db.citizens import upsert_citizen

router = APIRouter()

class RegisterCitizen(BaseModel):
    phone: str = Field(..., description="E.164 formatted phone number, must start with +91")
    pincode: str = Field(..., description="6-digit Indian pincode")
    name: Optional[str] = Field(None, description="Optional name")
    language: str = Field(..., description="Preferred language for communication")
    device_token: Optional[str] = Field(None, description="Optional FCM device token for notifications")

@router.post("/register")
async def register(request: Request, payload: RegisterCitizen):
    # 1. Validate phone number format
    if not payload.phone.startswith("+91") or len(payload.phone) != 13 or not payload.phone[1:].isdigit():
        raise HTTPException(status_code=400, detail="Invalid phone format. Must be +91 followed by 10 digits.")

    # 2. Validate pincode mapping
    pincode_info = validate_pincode(payload.pincode)
    if not pincode_info["valid"]:
        raise HTTPException(status_code=400, detail="Invalid pincode format")

    # 3. Handle unsupported states
    if not pincode_info["is_supported"]:
        return JSONResponse(status_code=403, content={
            "status": "region_not_supported",
            "message": "PRATINIDHI is currently available in Maharashtra, Delhi, Karnataka, Tamil Nadu, and Gujarat.",
            "your_state": pincode_info["state"],
            "your_district": pincode_info["district"],
            "coming_soon": True
        })

    # 4. Insert/Upsert into DB
    pool = request.app.state.pool
    citizen_record_id = await upsert_citizen(
        pool=pool,
        phone=payload.phone,
        name=payload.name or "Citizen",
        pincode=payload.pincode,
        state=pincode_info["state"],
        district=pincode_info["district"],
        city=pincode_info["district"],  # Fallback
        preferred_lang=payload.language,
        device_token=payload.device_token
    )

    # 5. Return Success
    # citizenId usually combines phone/pincode for easy flutter use, or uses the DB ID. We'll use the DB ID or a custom string.
    citizen_id = f"cit_{payload.pincode}_{payload.phone.replace('+91', '')}"

    return {
        "success": True,
        "citizenId": citizen_id,
        "state": pincode_info["state"],
        "district": pincode_info["district"],
        "message": f"Successfully registered for {pincode_info['state']}"
    }

@router.get("/pincode/{pincode}")
async def get_pincode_info(pincode: str):
    info = validate_pincode(pincode)
    return {
        "pincode": pincode,
        "state": info["state"],
        "district": info["district"],
        "city": info["district"],
        "is_supported": info["is_supported"],
        "available_languages": info["languages"]
    }

@router.get("/citizens/online")
async def get_online_citizens(request: Request):
    # This requires access to the websocket manager.
    # In FastAPI, you usually attach the manager to app state in main.py.
    # We will assume app.state.manager holds the ConnectionManager.
    manager = getattr(request.app.state, "manager", None)
    if not manager:
        return {"total_online": 0, "by_state": {}}
        
    # The active_connections dictionary maps websocket to citizen_info.  
    # To implement this, we loop through the meta attributes.
    total = len(manager.active_connections)
    by_state = {}
    
    # Using `manager.metadata` assuming we store { websocket: {"state": "...", ...} }
    # Since we edit realtime.py later, we'll design it to track state.
    for ws, meta in manager.connection_metadata.items():
        state = meta.get("state", "Unknown")
        by_state[state] = by_state.get(state, 0) + 1
        
    return {
        "total_online": total,
        "by_state": by_state
    }
