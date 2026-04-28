"""
Async Database Service using SQLAlchemy.
Supports both SQLite (aiosqlite) and PostgreSQL (asyncpg).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy import text, inspect
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from config import config

logger = logging.getLogger(__name__)


class DatabaseService:
    """Async database service for query execution."""

    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None

    async def connect(self) -> None:
        """Initialize the async engine and session factory."""
        db_url = config.database.database_url
        logger.info(f"Connecting to database: {config.database.db_type}")

        engine_kwargs = {"echo": config.debug}
        if config.database.db_type == "sqlite":
            engine_kwargs["connect_args"] = {"check_same_thread": False}

        self._engine = create_async_engine(db_url, **engine_kwargs)
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Database engine created")

    async def disconnect(self) -> None:
        """Dispose of the async engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            logger.info("Database engine disposed")

    @asynccontextmanager
    async def session(self) -> AsyncSession:
        """Provide a transactional session scope."""
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")
        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def execute_query(self, sql: str) -> Tuple[List[str], List[Dict[str, Any]], int]:
        """
        Execute a read-only SQL query and return results.

        Args:
            sql: SQL SELECT query string

        Returns:
            Tuple of (columns, rows_as_dicts, row_count)

        Raises:
            Exception: On query execution failure
        """
        async with self.session() as sess:
            result = await sess.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result.fetchall()]
            return columns, rows, len(rows)

    async def execute_script(self, script: str) -> None:
        """
        Execute a multi-statement SQL script (for schema/seed setup).

        Args:
            script: SQL script with semicolon-separated statements
        """
        statements = [s.strip() for s in script.split(";") if s.strip()]
        async with self.session() as sess:
            for stmt in statements:
                if stmt:
                    await sess.execute(text(stmt))
        logger.info(f"Executed script with {len(statements)} statements")

    async def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            async with self.session() as sess:
                result = await sess.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def get_schema_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Return schema information for all tables.

        Returns:
            Dict mapping table name → {columns, primary_key, foreign_keys}
        """
        schema_info = {}
        async with self.session() as sess:
            if config.database.db_type == "sqlite":
                tables_result = await sess.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                )
                table_names = [row[0] for row in tables_result.fetchall()]
            else:
                tables_result = await sess.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema='public' AND table_type='BASE TABLE'"
                    )
                )
                table_names = [row[0] for row in tables_result.fetchall()]

            for table_name in table_names:
                if config.database.db_type == "sqlite":
                    col_result = await sess.execute(text(f"PRAGMA table_info({table_name})"))
                    columns = [
                        {
                            "name": row[1],
                            "type": row[2],
                            "nullable": row[3] == 1,
                            "default": row[4],
                            "is_pk": row[5] == 1,
                        }
                        for row in col_result.fetchall()
                    ]
                else:
                    col_result = await sess.execute(
                        text(
                            "SELECT column_name, data_type, is_nullable, column_default "
                            "FROM information_schema.columns WHERE table_name=:t "
                            "ORDER BY ordinal_position"
                        ),
                        {"t": table_name},
                    )
                    columns = [
                        {
                            "name": row[0],
                            "type": row[1],
                            "nullable": row[2] == "YES",
                            "default": row[3],
                            "is_pk": False,
                        }
                        for row in col_result.fetchall()
                    ]

                schema_info[table_name] = {"columns": columns}

        return schema_info


# Singleton instance
db_service = DatabaseService()
