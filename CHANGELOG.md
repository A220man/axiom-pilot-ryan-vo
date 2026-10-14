# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-14

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
- Plugin Manifest Validator (planned): schema validation, SKILL.md frontmatter, path existence, MCP placeholders
- Diff Quality Analyzer (planned): import filtering detection, whitespace collapse detection
- OAuth Scope Auditor (planned): declared vs required scope checking
- Symlink Detector (planned): ~/.cursor/plugins/local symlink scanning
- Opt-in LLM explanations (planned): multi-provider support (OpenAI-compatible, Anthropic, Gemini, Ollama)
- Comprehensive test suites (backend pytest, frontend vitest)
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