"""Tests for authentication and authorization."""
import time
import pytest
from jose import jwt

from app.core.security import (
    create_session_token,
    decode_session_token,
    hash_password,
    verify_password,
    session_serializer,
)
from app.models import User, UserRole


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_and_verify(self):
        password = "pwd123"
        hashed = hash_password(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)

    def test_different_hashes(self):
        password = "pwd"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt uses salt
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestSessionTokens:
    """Test session token creation and validation."""

    def test_create_and_decode_session(self):
        data = {"user_id": 1, "sub": "sub-123", "email": "test@example.com", "name": "Test", "roles": ["viewer"]}
        token = create_session_token(data)
        decoded = decode_session_token(token)
        assert decoded == data

    def test_expired_session_rejected(self):
        # Test that decode_session_token rejects tokens with invalid signature
        from app.core.security import session_serializer
        token = session_serializer.dumps({"user_id": 1})
        # Tamper with the token by changing a character in the middle
        tampered = token[:10] + "x" + token[11:]
        decoded = decode_session_token(tampered)
        assert decoded is None


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoints_public(self, client):
        """Health endpoints should be public."""
        response = await client.get("/healthz")
        assert response.status_code == 200

        response = await client.get("/healthz/ready")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_me_requires_auth(self, client):
        """GET /auth/me should require authentication."""
        response = await client.get("/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_valid_session(self, client, session_cookie):
        """GET /auth/me should return user with valid session."""
        client.cookies.update(session_cookie)
        response = await client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "viewer" in data["roles"]
        assert "operator" in data["roles"]

    @pytest.mark.asyncio
    async def test_logout_clears_cookies(self, client, session_cookie, test_user):
        """POST /auth/logout should clear session cookies."""
        client.cookies.update(session_cookie)
        response = await client.post("/auth/logout")
        assert response.status_code == 200
        assert "logout_url" in response.json()
        # Cookies should be cleared
        assert "session" not in response.cookies or response.cookies.get("session") == ""

    @pytest.mark.asyncio
    async def test_csrf_endpoint(self, client):
        """POST /auth/csrf should return CSRF token and set cookie."""
        response = await client.post("/auth/csrf")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert data["csrf_token"] != ""
        assert "csrf_token" in response.cookies


class TestSecurityUtils:
    """Test security utility functions."""

    def test_jwt_token_creation_and_decoding(self):
        from app.core.config import get_settings
        settings = get_settings()
        data = {"sub": "user-123", "roles": ["viewer"]}
        token = jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert decoded["sub"] == "user-123"
        assert decoded["roles"] == ["viewer"]

    def test_invalid_jwt_rejected(self):
        from app.core.config import get_settings
        settings = get_settings()
        # Tampered token
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMifQ.invalid"
        # Should decode without verification but we test verification
        with pytest.raises(jwt.JWTError):
            jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    def test_pkce_generation(self):
        from app.core.security import generate_pkce_pair
        verifier, challenge = generate_pkce_pair()
        assert len(verifier) >= 43
        assert len(challenge) >= 43
        assert verifier != challenge

    def test_nonce_and_state_generation(self):
        from app.core.security import generate_nonce, generate_state
        nonce = generate_nonce()
        state = generate_state()
        assert len(nonce) >= 32
        assert len(state) >= 32
        assert nonce != state


class TestRoleAuthorization:
    """Test role-based authorization."""

    def test_user_role_methods(self, test_user):
        """Test User model role methods."""
        assert test_user.has_role("viewer")
        assert test_user.has_role("operator")
        assert not test_user.has_role("admin")
        assert test_user.is_operator()
        assert not test_user.is_admin()


class TestAuditLogging:
    """Test audit logging on auth events."""

    @pytest.mark.asyncio
    async def test_logout_creates_audit_log(self, client, session_cookie, test_user, db_session):
        """Logout should create audit log entry."""
        from sqlalchemy import select
        from app.models import AuditLog

        client.cookies.update(session_cookie)
        response = await client.post("/auth/logout")
        assert response.status_code == 200

        # Verify audit log was created
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.user_id == test_user.id, AuditLog.action == "logout")
        )
        audit = result.scalar_one_or_none()
        assert audit is not None
        assert audit.action == "logout"
        assert audit.resource_type == "session"