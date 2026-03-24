/* 
Regional Verification System Migrations 
Table setup for Pincode Tracking and Offline Notifications
*/

CREATE TABLE IF NOT EXISTS leader_receivers (
  id              SERIAL PRIMARY KEY,
  phone           VARCHAR(15) UNIQUE NOT NULL,
  name            VARCHAR(100),
  pincode         VARCHAR(6) NOT NULL,
  state           VARCHAR(50) NOT NULL,
  district        VARCHAR(100),
  city            VARCHAR(100),
  preferred_lang  VARCHAR(30) DEFAULT 'Hindi',
  is_app_user     BOOLEAN DEFAULT TRUE,
  device_token    VARCHAR(255),
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMP DEFAULT NOW(),
  last_seen       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_state ON leader_receivers(state);
CREATE INDEX IF NOT EXISTS idx_phone ON leader_receivers(phone);

-- User profiles table (rich citizen identity)
CREATE TABLE IF NOT EXISTS user_profiles (
  id           SERIAL PRIMARY KEY,
  phone        VARCHAR(15) UNIQUE NOT NULL REFERENCES leader_receivers(phone) ON DELETE CASCADE,
  name         VARCHAR(100),
  email        VARCHAR(150),
  language     VARCHAR(30) DEFAULT 'Hindi',
  state        VARCHAR(50),
  district     VARCHAR(100),
  pincode      VARCHAR(6),
  created_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_phone ON user_profiles(phone);

-- Per-citizen message history (permanent inbox)
CREATE TABLE IF NOT EXISTS user_messages (
  id           SERIAL PRIMARY KEY,
  phone        VARCHAR(15) NOT NULL REFERENCES user_profiles(phone) ON DELETE CASCADE,
  sender_state VARCHAR(50),
  title        VARCHAR(200),
  body         TEXT,
  message_type VARCHAR(30) DEFAULT 'announcement',
  is_read      BOOLEAN DEFAULT FALSE,
  received_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_messages_phone ON user_messages(phone);

-- Offline message delivery queue
CREATE TABLE IF NOT EXISTS offline_message_queue (
  id          SERIAL PRIMARY KEY,
  citizen_id  VARCHAR(50) NOT NULL,
  message     JSONB NOT NULL,
  created_at  TIMESTAMP DEFAULT NOW(),
  delivered   BOOLEAN DEFAULT FALSE,
  delivered_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_citizen_undelivered 
ON offline_message_queue(citizen_id, delivered) 
WHERE delivered = FALSE;

-- ─── SEED DATA: Two test leaders ──────────────────────────────────────────────
-- Leader 1: Maharashtra
INSERT INTO leader_receivers (phone, name, pincode, state, district, preferred_lang, is_app_user)
VALUES ('+911111111111', 'CM Maharashtra (Test Leader)', '411001', 'Maharashtra', 'Pune', 'Marathi', FALSE)
ON CONFLICT (phone) DO NOTHING;

-- Leader 2: Tamil Nadu
INSERT INTO leader_receivers (phone, name, pincode, state, district, preferred_lang, is_app_user)
VALUES ('+912222222222', 'CM Tamil Nadu (Test Leader)', '600001', 'Tamil Nadu', 'Chennai', 'Tamil', FALSE)
ON CONFLICT (phone) DO NOTHING;

