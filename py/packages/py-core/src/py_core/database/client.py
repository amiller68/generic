from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from enum import Enum as PyEnum

Base = declarative_base()

# NOTE: it is generally a good idea to make your database schema match your domain model
# At the moment all of our fields are the same, allowing us to interchange telebot types with our database types


class DatabaseExceptionType(PyEnum):
    conflict = "conflict"
    not_found = "not_found"
    invalid = "invalid"


class DatabaseException(Exception):
    def __init__(self, type: DatabaseExceptionType, message: str):
        self.message = message
        self.type = type

    def __str__(self):
        return f"{self.message}"

    @staticmethod
    def from_sqlalchemy_error(e):
        # If this is not an instance of a sqlalchemy error, just pass it through
        if not isinstance(e, Exception):
            return e

        error_msg = str(e).lower()

        # PostgreSQL error handling
        if any(
            phrase in error_msg
            for phrase in [
                "violates foreign key constraint",
                "foreign key constraint failed",
            ]
        ):
            return DatabaseException(DatabaseExceptionType.invalid, str(e))

        if any(
            phrase in error_msg
            for phrase in [
                "violates unique constraint",
                "unique constraint failed",
                "duplicate key",
            ]
        ):
            return DatabaseException(DatabaseExceptionType.conflict, str(e))

        if any(
            phrase in error_msg
            for phrase in [
                "no row was found for one",
                "no results found",
                "record not found",
            ]
        ):
            return DatabaseException(DatabaseExceptionType.not_found, str(e))

        if any(
            phrase in error_msg
            for phrase in ["violates check constraint", "check constraint failed"]
        ):
            return DatabaseException(DatabaseExceptionType.invalid, str(e))

        # Otherwise just pass through the error
        return e


# Database Initialization and helpers


# Simple Synchronous Database for setting up the database
class SyncDatabase:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)


class AsyncDatabase:
    def __init__(self, database_async_url):
        self.database_url = database_async_url

        # Configure engine with PostgreSQL settings
        self.engine = create_async_engine(
            database_async_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=False,
        )

        self.AsyncSession = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def initialize(self):
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self):
        session = self.AsyncSession()
        try:
            yield session
        finally:
            await session.close()

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
