import json
from datetime import datetime
import asyncpg

async def upsert_citizen(pool: asyncpg.Pool, phone: str, name: str, pincode: str, state: str, district: str, city: str, preferred_lang: str, device_token: str, email: str = None):
    # Step 1: Upsert into leader_receivers
    query1 = """
    INSERT INTO leader_receivers (phone, name, pincode, state, district, city, preferred_lang, device_token, last_seen)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
    ON CONFLICT (phone) DO UPDATE SET
        name = EXCLUDED.name, pincode = EXCLUDED.pincode,
        state = EXCLUDED.state, district = EXCLUDED.district,
        city = EXCLUDED.city, preferred_lang = EXCLUDED.preferred_lang,
        device_token = EXCLUDED.device_token, last_seen = NOW()
    RETURNING id;
    """
    # Step 2: Upsert into user_profiles (linked by phone)
    query2 = """
    INSERT INTO user_profiles (phone, name, email, language, state, district, pincode)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (phone) DO UPDATE SET
        name = EXCLUDED.name, email = EXCLUDED.email,
        language = EXCLUDED.language, state = EXCLUDED.state,
        district = EXCLUDED.district, pincode = EXCLUDED.pincode;
    """
    async with pool.acquire() as conn:
        record = await conn.fetchrow(query1, phone, name, pincode, state, district, city, preferred_lang, device_token)
        await conn.execute(query2, phone, name, email, preferred_lang, state, district, pincode)
        return record["id"]

async def get_citizen_phones_by_state(pool: asyncpg.Pool, state: str) -> list[str]:
    query = "SELECT phone FROM leader_receivers WHERE state = $1 AND is_active = TRUE AND is_app_user = TRUE"
    async with pool.acquire() as conn:
        records = await conn.fetch(query, state)
        return [r["phone"] for r in records]

async def save_message_to_inbox(pool: asyncpg.Pool, phone: str, sender_state: str, title: str, body: str, message_type: str = "announcement"):
    """Saves a received message permanently into the citizen's personal inbox."""
    query = """
    INSERT INTO user_messages (phone, sender_state, title, body, message_type)
    VALUES ($1, $2, $3, $4, $5)
    """
    async with pool.acquire() as conn:
        await conn.execute(query, phone, sender_state, title, body, message_type)

async def queue_offline_message(pool: asyncpg.Pool, citizen_id: str, message: dict):
    query = """
    INSERT INTO offline_message_queue (citizen_id, message)
    VALUES ($1, $2)
    """
    async with pool.acquire() as conn:
        await conn.execute(query, citizen_id, json.dumps(message))

async def get_undelivered_messages(pool: asyncpg.Pool, citizen_id: str) -> list[dict]:
    query = """
    SELECT id, message, created_at FROM offline_message_queue 
    WHERE citizen_id = $1 AND delivered = FALSE
    ORDER BY created_at ASC
    """
    async with pool.acquire() as conn:
        records = await conn.fetch(query, citizen_id)
        # Convert JSON strings to dicts
        results = []
        for r in records:
            msg_data = json.loads(r["message"])
            msg_data["msg_id"] = r["id"]
            msg_data["timestamp"] = r["created_at"].isoformat()
            results.append(msg_data)
        return results

async def mark_delivered(pool: asyncpg.Pool, citizen_id: str, message_ids: list[int]):
    if not message_ids:
        return
    query = """
    UPDATE offline_message_queue 
    SET delivered = TRUE, delivered_at = NOW() 
    WHERE citizen_id = $1 AND id = ANY($2::int[])
    """
    async with pool.acquire() as conn:
        await conn.execute(query, citizen_id, message_ids)
