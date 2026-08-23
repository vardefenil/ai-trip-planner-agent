"""
Database storage module for Yatra AI travel planner.
Stores sessions, conversations, and trip packages in PostgreSQL running in Docker,
with automatic SQLite fallback for maximum resilience.
"""
import os
import json
import logging
from datetime import datetime, timezone
import asyncpg
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_USER = os.getenv("POSTGRES_USER", "yatra")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yatra")
PG_DB = os.getenv("POSTGRES_DB", "yatradb")

SQLITE_PATH = Path(__file__).resolve().parent / "yatra_fallback.db"

_pg_pool: asyncpg.Pool | None = None
_use_sqlite = False


async def get_db_pool():
    """Get or initialize asyncpg connection pool."""
    global _pg_pool, _use_sqlite
    if _use_sqlite:
        return None
    if _pg_pool is None:
        try:
            _pg_pool = await asyncpg.create_pool(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASSWORD,
                database=PG_DB,
                min_size=1,
                max_size=10,
                timeout=5.0,
            )
            logger.info("Connected to PostgreSQL in Docker.")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed ({e}), using local SQLite fallback.")
            _use_sqlite = True
    return _pg_pool


def _init_sqlite():
    conn = sqlite3.connect(str(SQLITE_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            destination TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            msg_type TEXT NOT NULL,
            payload TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


async def init_db():
    """Initialize database tables in PostgreSQL or SQLite."""
    global _use_sqlite
    try:
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id VARCHAR(64) PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        destination VARCHAR(255),
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL
                    );
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id VARCHAR(64) PRIMARY KEY,
                        session_id VARCHAR(64) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                        role VARCHAR(32) NOT NULL,
                        content TEXT NOT NULL,
                        msg_type VARCHAR(32) NOT NULL,
                        payload JSONB,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL
                    );
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                """)
            logger.info("PostgreSQL tables initialized.")
            return
    except Exception as e:
        logger.warning(f"Postgres table init error: {e}. Falling back to SQLite.")
        _use_sqlite = True

    _init_sqlite()
    logger.info("SQLite fallback tables initialized.")


async def save_session(session_id: str, title: str, destination: str | None = None):
    """Create or update a conversation session."""
    now = datetime.now(timezone.utc)
    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO sessions (id, title, destination, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        destination = COALESCE(EXCLUDED.destination, sessions.destination),
                        updated_at = EXCLUDED.updated_at
                """, session_id, title, destination, now, now)
            return
        except Exception as e:
            logger.error(f"Error saving session to postgres: {e}")

    # SQLite fallback
    conn = sqlite3.connect(str(SQLITE_PATH))
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sessions (id, title, destination, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            destination = COALESCE(excluded.destination, sessions.destination),
            updated_at = excluded.updated_at
    """, (session_id, title, destination, now.isoformat(), now.isoformat()))
    conn.commit()
    conn.close()


async def save_message(
    session_id: str,
    message_id: str,
    role: str,
    content: str,
    msg_type: str = "text",
    payload: dict | list | None = None,
):
    """Save a chat message under a session."""
    now = datetime.now(timezone.utc)
    # Ensure session exists
    short_title = content[:40].replace("\n", " ").strip() if content else "New Travel Query"
    await save_session(session_id, short_title)

    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                payload_json = json.dumps(payload) if payload is not None else None
                await conn.execute("""
                    INSERT INTO messages (id, session_id, role, content, msg_type, payload, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        payload = EXCLUDED.payload
                """, message_id, session_id, role, content, msg_type, payload_json, now)
            return
        except Exception as e:
            logger.error(f"Error saving message to postgres: {e}")

    # SQLite fallback
    conn = sqlite3.connect(str(SQLITE_PATH))
    cur = conn.cursor()
    payload_str = json.dumps(payload) if payload is not None else None
    cur.execute("""
        INSERT INTO messages (id, session_id, role, content, msg_type, payload, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            content = excluded.content,
            payload = excluded.payload
    """, (message_id, session_id, role, content, msg_type, payload_str, now.isoformat()))
    conn.commit()
    conn.close()


async def list_sessions():
    """List all saved sessions sorted by most recent."""
    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, destination, created_at, updated_at
                    FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT 50
                """)
                return [
                    {
                        "id": r["id"],
                        "title": r["title"],
                        "destination": r["destination"],
                        "created_at": r["created_at"].isoformat() if r["created_at"] else "",
                        "updated_at": r["updated_at"].isoformat() if r["updated_at"] else "",
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error listing sessions from postgres: {e}")

    # SQLite fallback
    _init_sqlite()
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, destination, created_at, updated_at
        FROM sessions
        ORDER BY updated_at DESC
        LIMIT 50
    """)
    rows = cur.fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


async def get_session_messages(session_id: str):
    """Retrieve full message history for a session."""
    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, role, content, msg_type, payload, created_at
                    FROM messages
                    WHERE session_id = $1
                    ORDER BY created_at ASC
                """, session_id)
                return [
                    {
                        "id": r["id"],
                        "role": r["role"],
                        "content": r["content"],
                        "type": r["msg_type"],
                        "payload": json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"],
                        "timestamp": r["created_at"].isoformat() if r["created_at"] else "",
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error fetching messages from postgres: {e}")

    # SQLite fallback
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, role, content, msg_type, payload, created_at
        FROM messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    """, (session_id,))
    rows = cur.fetchall()
    result = []
    for r in rows:
        payload = json.loads(r["payload"]) if r["payload"] else None
        result.append({
            "id": r["id"],
            "role": r["role"],
            "content": r["content"],
            "type": r["msg_type"],
            "payload": payload,
            "timestamp": r["created_at"],
        })
    conn.close()
    return result


async def delete_session(session_id: str):
    """Delete a session and all its messages."""
    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM sessions WHERE id = $1", session_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting session from postgres: {e}")

    conn = sqlite3.connect(str(SQLITE_PATH))
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    cur.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    return True
