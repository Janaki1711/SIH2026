"""
database.py — iTantra M3 Web Demo SQLite Persistence

Stores message history and test results for the demo session.
"""

import sqlite3
import json
import time
import os

_DB_PATH = os.path.join(os.path.dirname(__file__), 'itantra_demo.db')


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
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
        conn.commit()


def save_message(msg: dict):
    """Persist a delivered message to SQLite."""
    m = msg.get("metrics", {})
    try:
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO messages (
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
    """Retrieve recent messages for history display."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[DB] Error reading messages: {e}")
        return []


def get_stats() -> dict:
    """Aggregate statistics from stored messages."""
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
                FROM messages
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
            conn.execute("DELETE FROM messages")
            conn.execute("DELETE FROM test_results")
            conn.commit()
    except Exception as e:
        print(f"[DB] Error clearing history: {e}")
