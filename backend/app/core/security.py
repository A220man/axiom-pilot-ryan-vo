"""Security utilities: password hashing, JWT tokens, CSRF, session management."""
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Serializers for session and CSRF tokens
session_serializer = URLSafeTimedSerializer(
    settings.secret_key,
    salt="session",
    signer_kwargs={"key_derivation": "hmac", "digest_method": "sha256"},
)
csrf_serializer = URLSafeTimedSerializer(
    settings.secret_key,
    salt="csrf",
    signer_kwargs={"key_derivation": "hmac", "digest_method": "sha256"},
)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.refresh_token_expire_days)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.JWTError:
        return None


def create_session_token(data: dict) -> str:
    """Create a signed session token (for cookie storage)."""
    return session_serializer.dumps(data)


def decode_session_token(token: str, max_age: int = 86400) -> Optional[dict]:
    """Decode and validate a session token."""
    try:
        return session_serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    return csrf_serializer.dumps({"token": secrets.token_urlsafe(32), "ts": time.time()})


def validate_csrf_token(token: str, max_age: int = 3600) -> bool:
    """Validate a CSRF token."""
    try:
        data = csrf_serializer.loads(token, max_age=max_age)
        return "token" in data
    except (BadSignature, SignatureExpired):
        return False


def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = secrets.token_urlsafe(64)
    import hashlib
    import base64
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    return code_verifier, code_challenge


def generate_nonce() -> str:
    """Generate a random nonce for OIDC."""
    return secrets.token_urlsafe(32)


def generate_state() -> str:
    """Generate a random state parameter for OIDC."""
    return secrets.token_urlsafe(32)