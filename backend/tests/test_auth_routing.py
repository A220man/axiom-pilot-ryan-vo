"""Regression tests for auth router registration.

The auth router must be mounted on the application so its session and CSRF
endpoints are reachable. Before the router was included, every ``/auth/*``
route returned 404 and was absent from the OpenAPI schema.
"""
import pytest


AUTH_PATHS = {"/auth/me", "/auth/logout", "/auth/csrf"}


def _registered_paths(app) -> set[str]:
    return {route.path for route in app.routes}


def test_auth_routes_registered(app):
    """The app must register the auth session/CSRF routes."""
    paths = _registered_paths(app)
    missing = AUTH_PATHS - paths
    assert not missing, f"auth routes not registered: {sorted(missing)}"


def test_auth_routes_in_openapi(app):
    """Registered auth routes must be advertised in the OpenAPI schema."""
    schema = app.openapi()
    missing = AUTH_PATHS - set(schema["paths"])
    assert not missing, f"auth paths missing from OpenAPI: {sorted(missing)}"


@pytest.mark.asyncio
async def test_me_returns_401_not_404(client):
    """Unauthenticated /auth/me must require auth (401), not be missing (404)."""
    response = await client.get("/auth/me")
    assert response.status_code == 401
