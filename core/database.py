from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from core.config import DATABASE_URL
from core.logger import get_logger

logger = get_logger(__name__)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def _ensure_database_exists():
    import asyncpg
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)
    db_name = parsed.path.lstrip("/")
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    user = parsed.username or "postgres"
    password = parsed.password or ""

    sys_conn = await asyncpg.connect(
        host=host, port=port, user=user, password=password, database="postgres",
    )
    try:
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            await sys_conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await sys_conn.close()


def run_migrations_sync():
    import subprocess
    import os
    import sys

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[alembic stderr] {result.stderr}")
        raise RuntimeError(f"Migration failed: {result.stderr}")


async def init_db():
    logger.info("Initializing database...")
    await _ensure_database_exists()
    import asyncio
    await asyncio.to_thread(run_migrations_sync)
    logger.info("Database initialization complete")
