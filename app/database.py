import asyncpg

from app.config import get_settings

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    global _pool
    settings = get_settings()
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        command_timeout=30,
    )
    async with _pool.acquire() as connection:
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
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


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
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO users (telegram_id, username, first_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            updated_at = NOW()
        RETURNING language
        """,
        telegram_id,
        username,
        first_name,
    )
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
