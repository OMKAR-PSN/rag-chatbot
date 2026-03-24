import pytest
from app.utils.pincode_validator import validate_pincode

def test_valid_maharashtra_pincode():
    res = validate_pincode("411038")
    assert res["valid"] is True
    assert res["state"] == "Maharashtra"
    assert res["is_supported"] is True

def test_valid_delhi_pincode():
    res = validate_pincode("110001")
    assert res["valid"] is True
    assert res["state"] == "Delhi"
    assert res["is_supported"] is True

def test_unsupported_state_pincode():
    res = validate_pincode("226010")  # UP
    assert res["valid"] is True
    assert res["state"] == "Uttar Pradesh"
    assert res["is_supported"] is False

def test_invalid_pincode_format():
    res = validate_pincode("00000")
    assert res["valid"] is False

def test_invalid_pincode_letters():
    res = validate_pincode("abcdef")
    assert res["valid"] is False

@pytest.mark.asyncio
async def test_register_citizen_success():
    # Placeholder for async TestClient
    pass

@pytest.mark.asyncio
async def test_register_citizen_unsupported():
    # Placeholder for async TestClient 403
    pass

@pytest.mark.asyncio
async def test_broadcast_to_state():
    # Placeholder for websocket manager unit test
    pass

@pytest.mark.asyncio
async def test_offline_queue():
    # Placeholder for DB offline queue test
    pass
