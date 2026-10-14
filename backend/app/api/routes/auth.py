"""Authentication routes: OIDC authorization code flow with PKCE."""
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_session_token,
    decode_session_token,
    generate_csrf_token,
    generate_nonce,
    generate_pkce_pair,
    generate_state,
    validate_csrf_token,
)
from app.models import AuditLog, User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()

# In-memory PKCE store (use Redis in production)
_pkce_store: dict[str, dict] = {}


def _store_pkce(state: str, code_verifier: str, nonce: str, redirect_after: str = "/") -> None:
    """Store PKCE parameters for the callback."""
    _pkce_store[state] = {
        "code_verifier": code_verifier,
        "nonce": nonce,
        "redirect_after": redirect_after,
        "created_at": datetime.now(timezone.utc).timestamp(),
    }


def _pop_pkce(state: str) -> dict | None:
    """Retrieve and remove PKCE parameters."""
    return _pkce_store.pop(state, None)


def _cleanup_pkce_store() -> None:
    """Remove expired PKCE entries (>10 min)."""
    now = datetime.now(timezone.utc).timestamp()
    expired = [k for k, v in _pkce_store.items() if now - v["created_at"] > 600]
    for k in expired:
        _pkce_store.pop(k, None)


@router.get("/login", summary="Initiate OIDC login")
async def login(request: Request, redirect_after: str = "/") -> RedirectResponse:
    """Start OIDC authorization code flow with PKCE."""
    _cleanup_pkce_store()

    if not settings.oidc_enabled:
        raise HTTPException(status_code=501, detail="OIDC not enabled")

    # Generate PKCE and state
    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()
    nonce = generate_nonce()

    _store_pkce(state, code_verifier, nonce, redirect_after)

    # Build authorization URL
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": " ".join(settings.oidc_scopes),
        "redirect_uri": settings.oidc_redirect_uri,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/auth?{urlencode(params)}"

    response = RedirectResponse(url=auth_url, status_code=302)
    return response


@router.get("/callback", summary="OIDC callback")
async def callback(
    request: Request,
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    """Handle OIDC callback, exchange code for tokens, create session."""
    _cleanup_pkce_store()

    if error:
        raise HTTPException(status_code=400, detail=f"OIDC error: {error} - {error_description}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    pkce_data = _pop_pkce(state)
    if not pkce_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")

    code_verifier = pkce_data["code_verifier"]
    nonce = pkce_data["nonce"]
    redirect_after = pkce_data.get("redirect_after", "/")

    # Exchange code for tokens
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            f"{settings.oidc_issuer_url}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.oidc_redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400, detail=f"Token exchange failed: {token_response.text}"
        )

    tokens = token_response.json()
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")

    if not id_token:
        raise HTTPException(status_code=400, detail="No ID token in response")

    # Validate ID token (simplified - in production use jose with JWKS)
    # For now, decode without verification to extract claims
    from jose import jwt
    try:
        claims = jwt.get_unverified_claims(id_token)
    except jwt.JWTError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID token: {e}")

    # Verify nonce
    if claims.get("nonce") != nonce:
        raise HTTPException(status_code=400, detail="Nonce mismatch")

    # Extract user info
    sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name") or claims.get("preferred_username") or email
    preferred_username = claims.get("preferred_username")
    realm_roles = claims.get("realm_access", {}).get("roles", [])

    if not sub or not email:
        raise HTTPException(status_code=400, detail="Missing required claims")

    # Map Keycloak roles to app roles
    app_roles = [UserRole.VIEWER.value]
    if "admin" in realm_roles:
        app_roles.append(UserRole.ADMIN.value)
    if "operator" in realm_roles:
        app_roles.append(UserRole.OPERATOR.value)

    # Upsert user
    result = await db.execute(select(User).where(User.sub == sub))
    user = result.scalar_one_or_none()

    if user:
        user.email = email
        user.name = name
        user.preferred_username = preferred_username
        user.roles = ",".join(app_roles)
        user.last_login = datetime.now(timezone.utc)
    else:
        user = User(
            sub=sub,
            email=email,
            name=name,
            preferred_username=preferred_username,
            roles=",".join(app_roles),
            last_login=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.flush()

    # Create session token
    session_data = {
        "user_id": user.id,
        "sub": user.sub,
        "email": user.email,
        "name": user.name,
        "roles": user.get_roles(),
    }
    session_token = create_session_token(session_data)

    # Set session cookie
    response = RedirectResponse(url=f"{settings.frontend_url}{redirect_after}", status_code=302)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=settings.refresh_token_expire_days * 86400,
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )

    # Set CSRF cookie
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=3600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="session",
        details=json.dumps({"provider": "oidc"}),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)

    return response


@router.post("/logout", summary="Logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Clear session and redirect to OIDC logout."""
    session_cookie = request.cookies.get(settings.session_cookie_name)
    user_id = None

    if session_cookie:
        session_data = decode_session_token(session_cookie)
        if session_data:
            user_id = session_data.get("user_id")

    # Clear cookies
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")

    # Audit log
    if user_id:
        audit = AuditLog(
            user_id=user_id,
            action="logout",
            resource_type="session",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(audit)

    # Build OIDC logout URL
    logout_url = (
        f"{settings.oidc_logout_uri}?post_logout_redirect_uri={settings.frontend_url}"
    )

    return {"logout_url": logout_url, "message": "Logged out successfully"}


@router.get("/me", summary="Get current user")
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db_session)) -> dict:
    """Get current authenticated user from session."""
    session_cookie = request.cookies.get(settings.session_cookie_name)
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = decode_session_token(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session data")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user.id,
        "sub": user.sub,
        "email": user.email,
        "name": user.name,
        "preferred_username": user.preferred_username,
        "roles": user.get_roles(),
    }


@router.post("/csrf", summary="Get CSRF token")
async def get_csrf_token(response: Response) -> dict:
    """Generate and return a new CSRF token."""
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=3600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return {"csrf_token": csrf_token}


def require_auth(request: Request) -> dict:
    """Dependency to require authentication."""
    session_cookie = request.cookies.get(settings.session_cookie_name)
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = decode_session_token(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return session_data


def require_role(*roles: str):
    """Dependency factory to require specific role(s)."""
    def checker(request: Request) -> dict:
        session_data = require_auth(request)
        user_roles = session_data.get("roles", [])
        if not any(r in user_roles for r in roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return session_data
    return checker


def verify_csrf(request: Request) -> None:
    """Verify CSRF token for state-changing operations."""
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_cookie or not csrf_header:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    if not validate_csrf_token(csrf_cookie):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    if csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="CSRF token mismatch")