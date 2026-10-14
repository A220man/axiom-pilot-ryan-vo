"""Pytest configuration and fixtures."""
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import PendingRollbackError

from app.core.config import Settings
from app.core.database import Base, get_db_session
from app.main import create_app
from app.models import User


@pytest.fixture(scope="session")
def test_settings():
    """Create test settings with in-memory database."""
    return Settings(
        environment="test",
        debug=True,
        secret_key="test-secret-key-for-testing-only",
        oidc_client_secret="test-client-secret",
        database_url="sqlite+aiosqlite:///:memory:",
        oidc_enabled=False,
    )


@pytest.fixture(scope="function")
async def test_engine(test_settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session_maker(test_engine):
    """Create test session factory."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


@pytest.fixture(scope="function")
async def db_session(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for testing."""
    async with test_session_maker() as session:
        try:
            yield session
        finally:
            # Always rollback to clean up any pending transaction
            try:
                await session.rollback()
            except Exception:
                pass
            await session.close()


@pytest.fixture(scope="function")
def app(test_settings, test_session_maker):
    """Create test FastAPI app with overridden dependencies."""
    from app.core.config import get_settings
    from app.core.database import get_db_session as get_db_session_orig

    def override_get_settings():
        return test_settings

    async def override_get_db_session():
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app = create_app()
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_db_session_orig] = override_get_db_session

    yield app

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in database."""
    user = User(
        sub="test-sub-123",
        email="test@example.com",
        name="Test User",
        preferred_username="testuser",
        roles="viewer,operator",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def session_cookie(test_user):
    """Create a valid session cookie for test user."""
    from app.core.security import create_session_token
    session_data = {
        "user_id": test_user.id,
        "sub": test_user.sub,
        "email": test_user.email,
        "name": test_user.name,
        "roles": test_user.get_roles(),
    }
    token = create_session_token(session_data)
    return {"session": token}