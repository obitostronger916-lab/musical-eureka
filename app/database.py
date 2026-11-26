import asyncpg

from app.config import get_settings

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    global _pool
    if _pool is not None:
        return
    settings = get_settings()
    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        ssl="require",
        server_settings={"channel_binding": "disable"},
        min_size=1,
        max_size=5,
        command_timeout=30,
        timeout=30,
    )
    try:
        async with pool.acquire() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT NOT NULL DEFAULT '',
                    language TEXT NOT NULL DEFAULT 'uz'
                        CHECK (language IN ('uz', 'ru', 'en')),
                    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_request_at TIMESTAMPTZ
                );

                ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS last_request_at TIMESTAMPTZ;

                CREATE TABLE IF NOT EXISTS chats (
                    chat_id BIGINT PRIMARY KEY,
                    chat_type TEXT NOT NULL,
                    title TEXT,
                    username TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS request_logs (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    chat_id BIGINT,
                    request_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ok',
                    detail TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_request_logs_created
                    ON request_logs (created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_users_created
                    ON users (created_at DESC);

                """
            )
    except Exception:
        await pool.close()
        raise
    _pool = pool


async def close() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database is not connected")
    return _pool


async def save_user(
    telegram_id: int,
    username: str | None,
    first_name: str,
) -> str:
    row = await get_pool().fetchrow(
        """
        INSERT INTO users (telegram_id, username, first_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            updated_at = NOW()
        RETURNING language, is_blocked
        """,
        telegram_id,
        username,
        first_name,
    )
    # Blocking is checked separately by handlers; always preserve the user's
    # selected language for localized restriction messages.
    return row["language"]


async def set_user_language(telegram_id: int, language: str) -> None:
    if language not in {"uz", "ru", "en"}:
        raise ValueError("Unsupported language")
    await get_pool().execute(
        """
        UPDATE users
        SET language = $2, updated_at = NOW()
        WHERE telegram_id = $1
        """,
        telegram_id,
        language,
    )


async def get_user_language(telegram_id: int) -> str:
    value = await get_pool().fetchval(
        "SELECT language FROM users WHERE telegram_id = $1",
        telegram_id,
    )
    return value or "uz"


async def is_user_blocked(telegram_id: int) -> bool:
    value = await get_pool().fetchval(
        "SELECT is_blocked FROM users WHERE telegram_id = $1",
        telegram_id,
    )
    return bool(value)


async def save_chat(chat_id: int, chat_type: str, title: str | None, username: str | None) -> None:
    await get_pool().execute(
        """
        INSERT INTO chats (chat_id, chat_type, title, username)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (chat_id) DO UPDATE SET
            chat_type = EXCLUDED.chat_type,
            title = EXCLUDED.title,
            username = EXCLUDED.username,
            is_active = TRUE,
            last_seen_at = NOW()
        """,
        chat_id, chat_type, title, username,
    )


async def log_request(
    telegram_id: int | None,
    chat_id: int | None,
    request_type: str,
    status: str = "ok",
    detail: str | None = None,
) -> None:
    await get_pool().execute(
        """
        INSERT INTO request_logs (telegram_id, chat_id, request_type, status, detail)
        VALUES ($1, $2, $3, $4, $5)
        """,
        telegram_id, chat_id, request_type, status, (detail or "")[:500] or None,
    )


async def allow_request(telegram_id: int, cooldown_seconds: int = 2) -> bool:
    row = await get_pool().fetchrow(
        """
        UPDATE users
        SET last_request_at = NOW()
        WHERE telegram_id = $1
          AND (
            last_request_at IS NULL OR
            last_request_at < NOW() - ($2 * INTERVAL '1 second')
          )
        RETURNING telegram_id
        """,
        telegram_id, cooldown_seconds,
    )
    return row is not None


async def admin_stats() -> dict[str, int]:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT
            (SELECT COUNT(*) FROM users) AS user_count,
            (SELECT COUNT(*) FROM chats WHERE chat_type IN ('group', 'supergroup')) AS group_count,
            (SELECT COUNT(*) FROM request_logs) AS request_count,
            (SELECT COUNT(*) FROM request_logs WHERE status = 'error') AS error_count
        """
    )
    return {
        "users": row["user_count"],
        "groups": row["group_count"],
        "requests": row["request_count"],
        "errors": row["error_count"],
    }


async def set_user_blocked(telegram_id: int, blocked: bool) -> bool:
    result = await get_pool().execute(
        "UPDATE users SET is_blocked = $2, updated_at = NOW() WHERE telegram_id = $1",
        telegram_id, blocked,
    )
    return result.endswith("1")


async def latest_users(limit: int = 10) -> list[asyncpg.Record]:
    safe_limit = max(1, min(limit, 20))
    return await get_pool().fetch(
        """
        SELECT telegram_id, username, first_name, language, is_blocked, created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT $1
        """,
        safe_limit,
    )


async def latest_requests(limit: int = 10) -> list[asyncpg.Record]:
    safe_limit = max(1, min(limit, 20))
    return await get_pool().fetch(
        """
        SELECT telegram_id, chat_id, request_type, status, detail, created_at
        FROM request_logs
        ORDER BY created_at DESC
        LIMIT $1
        """,
        safe_limit,
    )
