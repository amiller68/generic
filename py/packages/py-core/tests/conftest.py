"""Pytest configuration and fixtures for py-core tests.

Placeholder fixtures for future database integration tests.
Uncomment and configure when a test database is available.

Example usage:

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from py_core.database.client import Base

    @pytest.fixture(scope="session")
    def event_loop():
        import asyncio
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture(scope="session")
    async def test_engine():
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
        await engine.dispose()

    @pytest.fixture
    async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
        async_session = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            yield session
            await session.rollback()
"""
