# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.0.0] - 2026-10-21

### Added
- FastAPI backend with SQLite persistence and SQLAlchemy async ORM
- React + TypeScript + Vite frontend with typed API client
- OIDC authentication via Keycloak (authorization code flow + PKCE)
- Backend-managed sessions with HttpOnly SameSite cookies and CSRF protection
- Role-based authorization: viewer, operator, admin
- Health check endpoints (`/healthz`, `/healthz/ready`)
- Audit logging for login/logout and important actions
- Docker Compose with Keycloak, backend, frontend services
- Keycloak realm export with pre-configured roles, clients, and demo users
- Comprehensive test suites (backend pytest: 23 tests, frontend vitest: 4 tests)
- CI workflow (GitHub Actions): backend tests, frontend build/test, Docker builds

### Security
- Session cookies: HttpOnly, SameSite=Lax, Secure in production
- CSRF protection on all state-changing endpoints
- PKCE for OIDC authorization code flow
- JWT tokens with short expiry (access: 30 min, refresh: 7 days)
- bcrypt password hashing (for local auth fallback)
- No tokens in localStorage; PKCE verifier in sessionStorage only
- Demo mode explicitly blocked in production environment
- Secret keys required in production; startup validation

### Infrastructure
- Non-root Docker users for all services
- Health checks on all containers
- Persistent volumes for SQLite and Keycloak data
- Development ports bound to 127.0.0.1 only
- .env.example with blank credentials
- .gitignore excludes .venv, node_modules, dist, databases, secrets

## Roadmap (planned, not implemented)
- Plugin Manifest Validator: schema validation, SKILL.md frontmatter, path existence, MCP placeholders
- Diff Quality Analyzer (issue #472): import filtering detection, whitespace collapse detection
- OAuth Scope Auditor (issue #385): declared vs required scope checking
- Symlink Detector (issue #35): ~/.cursor/plugins/local symlink scanning