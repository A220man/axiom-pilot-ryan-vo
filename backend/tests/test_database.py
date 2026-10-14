"""Tests for database models and persistence."""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User, UserRole


@pytest.mark.asyncio
async def test_user_creation_and_roles(db_session: AsyncSession):
    """Test user creation with roles."""
    user = User(
        sub="test-sub-123",
        email="test@example.com",
        name="Test User",
        preferred_username="testuser",
        roles="viewer,operator",
    )
    db_session.add(user)
    await db_session.flush()

    assert user.id is not None
    assert user.get_roles() == ["viewer", "operator"]
    assert user.has_role("viewer")
    assert user.has_role("operator")
    assert not user.has_role("admin")
    assert user.is_operator()
    assert not user.is_admin()


@pytest.mark.asyncio
async def test_user_role_admin_composite(db_session: AsyncSession):
    """Test admin role includes operator and viewer."""
    user = User(
        sub="admin-sub",
        email="admin@example.com",
        name="Admin User",
        roles="admin",
    )
    db_session.add(user)
    await db_session.flush()

    assert user.has_role("admin")
    assert user.is_admin()
    assert user.is_operator()


@pytest.mark.asyncio
async def test_audit_log_creation(db_session: AsyncSession):
    """Test audit log persistence."""
    user = User(
        sub="audit-sub",
        email="audit@example.com",
        name="Audit User",
        roles="viewer",
    )
    db_session.add(user)
    await db_session.flush()

    audit = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="session",
        details='{"provider": "oidc"}',
        ip_address="127.0.0.1",
        user_agent="test-agent",
    )
    db_session.add(audit)
    await db_session.flush()

    assert audit.id is not None
    assert audit.user_id == user.id
    assert audit.action == "login"
    assert audit.created_at is not None


@pytest.mark.asyncio
async def test_user_unique_sub_constraint(db_session: AsyncSession):
    """Test unique constraint on sub."""
    user1 = User(sub="unique-sub", email="unique1@example.com", name="User 1", roles="viewer")
    user2 = User(sub="unique-sub", email="unique2@example.com", name="User 2", roles="viewer")
    db_session.add(user1)
    db_session.add(user2)

    with pytest.raises(Exception):
        await db_session.flush()


@pytest.mark.asyncio
async def test_user_unique_email_constraint(db_session: AsyncSession):
    """Test unique constraint on email."""
    user1 = User(sub="sub1", email="dup@example.com", name="User 1", roles="viewer")
    user2 = User(sub="sub2", email="dup@example.com", name="User 2", roles="viewer")
    db_session.add(user1)
    db_session.add(user2)

    with pytest.raises(Exception):
        await db_session.flush()


@pytest.mark.asyncio
async def test_user_timestamps(db_session: AsyncSession):
    """Test automatic timestamp updates."""
    user = User(sub="ts-sub", email="ts@example.com", name="TS User", roles="viewer")
    db_session.add(user)
    await db_session.flush()

    created = user.created_at
    updated = user.updated_at
    assert created is not None
    assert updated is not None
    # Created and updated should be very close (within 1 second)
    assert abs((created - updated).total_seconds()) < 1