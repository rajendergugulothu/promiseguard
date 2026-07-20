"""
Database setup — PostgreSQL 16 + pgvector via Neon.
Neon SSL fix: strip sslmode and channel_binding from URL,
pass ssl via connect_args (asyncpg does not accept them as query params).
"""

import os
from urllib.parse import urlparse, parse_qs, urlencode
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text


def _clean_database_url(url: str) -> tuple[str, dict]:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params.pop("sslmode", None)
    params.pop("channel_binding", None)
    clean_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = parsed._replace(query=clean_query).geturl()
    connect_args = {"ssl": "require"} if "neon" in url else {}
    return clean_url, connect_args


_raw_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost/promiseguard")
if "postgresql://" in _raw_url and "asyncpg" not in _raw_url:
    _raw_url = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

DATABASE_URL, _connect_args = _clean_database_url(_raw_url)

engine = create_async_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_pgvector(conn):
    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
