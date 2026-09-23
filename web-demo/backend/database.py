"""
database.py — iTantra M3 Web Demo SQLite Persistence

Stores message history and test results for the demo session.
Also provides the multi-user chat schema (users, conversations, messages).
"""

import sqlite3
import json
import time
import os
import uuid as _uuid

_DB_PATH = os.path.join(os.path.dirname(__file__), 'itantra_demo.db')


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_legacy_messages(conn: sqlite3.Connection) -> None:
    """Resolve the legacy `messages` table name collision.

    Early versions of the demo pipeline stored wire-packet history in a
    table called `messages` (columns: sender_location, receiver_location,
    …). The multi-user chat now owns that table name with a completely
    different schema (conversation_id, sender_id, …). A database created
    before the chat existed still has the legacy table, which makes
    `CREATE TABLE IF NOT EXISTS messages (chat schema)` a no-op and every
    subsequent chat query fail.

    Migration (runs on every startup, idempotent, lossless):
      1. `messages` absent, or already the chat schema → nothing to do.
      2. Legacy `messages` found and `demo_messages` missing → rename it
         to `demo_messages` (the table the legacy code now writes to).
      3. Legacy `messages` found and `demo_messages` exists → copy any
         rows not already there (NULL-safe match on timestamp + text),
         then rename the old table to `messages_legacy` so the name is
         free for the chat schema. No rows are ever dropped.
    """
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
    ).fetchone()
    if not row:
        return
    cols = [r[1] for r in conn.execute("PRAGMA table_info(messages)")]
    if "conversation_id" in cols:
        return  # already the chat schema

    demo_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='demo_messages'"
    ).fetchone()
    if not demo_exists:
        conn.execute("ALTER TABLE messages RENAME TO demo_messages")
        print("[DB] Migrated legacy 'messages' table → 'demo_messages'")
        return

    # Both legacy-shaped tables exist: preserve rows, then free the name.
    conn.execute("""
        INSERT INTO demo_messages
        SELECT * FROM messages
        WHERE NOT EXISTS (
            SELECT 1 FROM demo_messages d
            WHERE d.timestamp IS messages.timestamp
              AND d.original_text IS messages.original_text
        )
    """)
    conn.execute("ALTER TABLE messages RENAME TO messages_legacy")
    print("[DB] Moved legacy 'messages' rows into 'demo_messages'; "
          "old table kept as 'messages_legacy'")


def init_db():
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        _migrate_legacy_messages(conn)

        # ── Legacy demo tables ─────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS demo_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                sender_location TEXT NOT NULL,
                receiver_location TEXT NOT NULL,
                source_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                original_text TEXT NOT NULL,
                translated_text TEXT,
                translation_mode TEXT,
                raw_text_bytes INTEGER,
                compressed_payload_bytes INTEGER,
                proto_packet_bytes INTEGER,
                final_packet_bytes INTEGER,
                compression_ratio REAL,
                total_latency_ms REAL,
                stt_ms REAL,
                compression_ms REAL,
                serialization_ms REAL,
                encryption_ms REAL,
                decryption_ms REAL,
                decode_ms REAL,
                decompression_ms REAL,
                translation_ms REAL,
                delivery_status TEXT DEFAULT 'DELIVERED',
                priority INTEGER DEFAULT 0,
                sequence_number INTEGER,
                callsign TEXT,
                crc_value TEXT,
                hex_packet TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                test_type TEXT NOT NULL,
                location TEXT NOT NULL,
                results TEXT NOT NULL
            )
        """)

        # ── Chat: users ────────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                phone TEXT UNIQUE,
                display_name TEXT,
                preferred_language TEXT DEFAULT 'en',
                created_at REAL,
                last_seen REAL
            )
        """)

        # ── Chat: conversations ────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                type TEXT DEFAULT 'direct',
                created_at REAL,
                updated_at REAL
            )
        """)

        # ── Chat: conversation_members ─────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_members (
                conversation_id TEXT,
                user_id TEXT,
                joined_at REAL,
                PRIMARY KEY (conversation_id, user_id)
            )
        """)

        # ── Chat: messages ─────────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                sender_id TEXT,
                original_text TEXT,
                source_language TEXT,
                target_language TEXT,
                semantic_payload TEXT,
                translated_text TEXT,
                timestamp REAL,
                status TEXT DEFAULT 'sent',
                priority INTEGER DEFAULT 0
            )
        """)

        # ── Indexes ────────────────────────────────────────────────────────
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages(conversation_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_members_user ON conversation_members(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")

        conn.commit()


def save_message(msg: dict):
    """Persist a delivered demo message to SQLite (legacy demo pipeline)."""
    m = msg.get("metrics", {})
    try:
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO demo_messages (
                    timestamp, sender_location, receiver_location,
                    source_language, target_language, original_text, translated_text,
                    translation_mode, raw_text_bytes, compressed_payload_bytes,
                    proto_packet_bytes, final_packet_bytes, compression_ratio,
                    total_latency_ms, stt_ms, compression_ms, serialization_ms,
                    encryption_ms, decryption_ms, decode_ms, decompression_ms,
                    translation_ms, delivery_status, priority, sequence_number,
                    callsign, crc_value, hex_packet
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                msg.get("timestamp", time.time()),
                msg.get("from_location", ""),
                msg.get("to_location", ""),
                msg.get("source_language", ""),
                msg.get("target_language", ""),
                msg.get("original_text", ""),
                msg.get("translated_text", ""),
                msg.get("translation_mode", ""),
                m.get("raw_text_bytes"),
                m.get("compressed_payload_bytes"),
                m.get("proto_packet_bytes"),
                m.get("final_packet_bytes"),
                m.get("compression_ratio"),
                m.get("total_latency_ms"),
                m.get("stt_ms"),
                m.get("compression_ms"),
                m.get("serialization_ms"),
                m.get("encryption_ms"),
                m.get("decryption_ms"),
                m.get("decode_ms"),
                m.get("decompression_ms"),
                m.get("translation_ms"),
                msg.get("delivery_status", "DELIVERED"),
                msg.get("priority", 0),
                msg.get("sequence"),
                msg.get("callsign"),
                msg.get("crc_value"),
                msg.get("hex", "")[:512],  # Truncate for storage
            ))
            conn.commit()
    except Exception as e:
        print(f"[DB] Error saving message: {e}")


def save_test_result(test_type: str, location: str, results: dict):
    """Persist a test result."""
    try:
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO test_results (timestamp, test_type, location, results)
                VALUES (?, ?, ?, ?)
            """, (time.time(), test_type, location, json.dumps(results)))
            conn.commit()
    except Exception as e:
        print(f"[DB] Error saving test result: {e}")


def get_recent_messages(limit: int = 50) -> list[dict]:
    """Retrieve recent messages for history display (legacy demo pipeline)."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM demo_messages ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[DB] Error reading messages: {e}")
        return []


def get_stats() -> dict:
    """Aggregate statistics from stored messages (legacy demo pipeline)."""
    try:
        with _get_conn() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_messages,
                    AVG(total_latency_ms) as avg_latency_ms,
                    MIN(total_latency_ms) as min_latency_ms,
                    MAX(total_latency_ms) as max_latency_ms,
                    AVG(compression_ratio) as avg_compression_ratio,
                    AVG(final_packet_bytes) as avg_packet_bytes
                FROM demo_messages
                WHERE delivery_status = 'DELIVERED'
            """).fetchone()
            if row:
                return dict(row)
            return {}
    except Exception as e:
        print(f"[DB] Error reading stats: {e}")
        return {}


def clear_history():
    """Clear all stored messages (for demo reset)."""
    try:
        with _get_conn() as conn:
            conn.execute("DELETE FROM demo_messages")
            conn.execute("DELETE FROM test_results")
            conn.commit()
    except Exception as e:
        print(f"[DB] Error clearing history: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Chat: User helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_user(user_id: str, phone: str, display_name: str, preferred_language: str = 'en') -> None:
    """Insert a new user row or update existing by phone."""
    now = time.time()
    try:
        with _get_conn() as conn:
            conn.execute(
                """INSERT INTO users (id, phone, display_name, preferred_language, created_at, last_seen)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(phone) DO UPDATE SET
                       id=excluded.id,
                       display_name=excluded.display_name,
                       preferred_language=excluded.preferred_language,
                       last_seen=excluded.last_seen""",
                (user_id, phone, display_name, preferred_language, now, now)
            )
            conn.commit()
    except Exception as e:
        print(f"[DB] create_user error: {e}")



def get_user_by_phone(phone: str) -> dict | None:
    """Return user row as dict or None."""
    try:
        with _get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[DB] get_user_by_phone error: {e}")
        return None


def get_user_by_id(user_id: str) -> dict | None:
    """Return user row as dict or None."""
    try:
        with _get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[DB] get_user_by_id error: {e}")
        return None


def update_user_language(user_id: str, language: str) -> None:
    """Update a user's preferred_language and last_seen."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE users SET preferred_language = ?, last_seen = ? WHERE id = ?",
                (language, time.time(), user_id)
            )
            conn.commit()
    except Exception as e:
        print(f"[DB] update_user_language error: {e}")


def update_user_profile(user_id: str, display_name: str, preferred_language: str) -> None:
    """Mirror both profile fields into the users row (re-login / PATCH /me)."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE users SET display_name = ?, preferred_language = ?, last_seen = ? WHERE id = ?",
                (display_name, preferred_language, time.time(), user_id)
            )
            conn.commit()
    except Exception as e:
        print(f"[DB] update_user_profile error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Chat: Conversation helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_direct_conversation(user_a_id: str, user_b_id: str) -> str:
    """Return existing direct conversation_id for the pair, or create one."""
    try:
        with _get_conn() as conn:
            # Find a 'direct' conversation that contains both users
            row = conn.execute("""
                SELECT cm1.conversation_id
                FROM conversation_members cm1
                JOIN conversation_members cm2 ON cm1.conversation_id = cm2.conversation_id
                JOIN conversations c ON c.id = cm1.conversation_id
                WHERE cm1.user_id = ? AND cm2.user_id = ? AND c.type = 'direct'
                LIMIT 1
            """, (user_a_id, user_b_id)).fetchone()

            if row:
                return row["conversation_id"]

            # Create a new direct conversation
            conv_id = str(_uuid.uuid4())
            now = time.time()
            conn.execute(
                "INSERT INTO conversations (id, type, created_at, updated_at) VALUES (?, 'direct', ?, ?)",
                (conv_id, now, now)
            )
            conn.execute(
                "INSERT INTO conversation_members (conversation_id, user_id, joined_at) VALUES (?, ?, ?)",
                (conv_id, user_a_id, now)
            )
            conn.execute(
                "INSERT INTO conversation_members (conversation_id, user_id, joined_at) VALUES (?, ?, ?)",
                (conv_id, user_b_id, now)
            )
            conn.commit()
            return conv_id
    except Exception as e:
        print(f"[DB] get_or_create_direct_conversation error: {e}")
        raise


def save_chat_message(message_dict: dict) -> str:
    """Persist a chat message. Returns the message_id."""
    try:
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO messages (id, conversation_id, sender_id, original_text,
                    source_language, target_language, semantic_payload, translated_text,
                    timestamp, status, priority)
                VALUES (:id, :conversation_id, :sender_id, :original_text,
                    :source_language, :target_language, :semantic_payload, :translated_text,
                    :timestamp, :status, :priority)
            """, {
                "id": message_dict.get("id", str(_uuid.uuid4())),
                "conversation_id": message_dict.get("conversation_id", ""),
                "sender_id": message_dict.get("sender_id", ""),
                "original_text": message_dict.get("original_text", ""),
                "source_language": message_dict.get("source_language", "en"),
                "target_language": message_dict.get("target_language", "en"),
                "semantic_payload": message_dict.get("semantic_payload", ""),
                "translated_text": message_dict.get("translated_text", ""),
                "timestamp": message_dict.get("timestamp", time.time()),
                "status": message_dict.get("status", "sent"),
                "priority": message_dict.get("priority", 0),
            })
            # Update conversation updated_at
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (message_dict.get("timestamp", time.time()), message_dict.get("conversation_id"))
            )
            conn.commit()
        return message_dict["id"]
    except Exception as e:
        print(f"[DB] save_chat_message error: {e}")
        raise


def get_conversation_messages(conversation_id: str, limit: int = 50) -> list[dict]:
    """Return the most recent `limit` messages in a conversation, oldest first."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit)).fetchall()
            return list(reversed([dict(r) for r in rows]))
    except Exception as e:
        print(f"[DB] get_conversation_messages error: {e}")
        return []


def get_user_conversations(user_id: str) -> list[dict]:
    """Return all conversations for a user with a last_message preview."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("""
                SELECT c.id, c.type, c.created_at, c.updated_at,
                       m.original_text AS last_message_text,
                       m.timestamp AS last_message_ts,
                       m.sender_id AS last_message_sender
                FROM conversations c
                JOIN conversation_members cm ON cm.conversation_id = c.id
                LEFT JOIN messages m ON m.id = (
                    SELECT id FROM messages
                    WHERE conversation_id = c.id
                    ORDER BY timestamp DESC
                    LIMIT 1
                )
                WHERE cm.user_id = ?
                ORDER BY c.updated_at DESC
            """, (user_id,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[DB] get_user_conversations error: {e}")
        return []


def get_conversation_members(conversation_id: str) -> list[str]:
    """Return list of user_ids who are members of the conversation."""
    try:
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT user_id FROM conversation_members WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchall()
            return [r["user_id"] for r in rows]
    except Exception as e:
        print(f"[DB] get_conversation_members error: {e}")
        return []


def is_conversation_member(conversation_id: str, user_id: str) -> bool:
    """Return True if user_id is a member of conversation_id."""
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
                (conversation_id, user_id)
            ).fetchone()
            return row is not None
    except Exception as e:
        print(f"[DB] is_conversation_member error: {e}")
        return False
