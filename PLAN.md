# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-skeleton

## Roadmap

### core-skeleton — FastAPI/React skeleton with auth, DB, and Docker

Status: in_progress

Acceptance:
- Backend FastAPI app starts with SQLite DB
- Frontend React+TS+Vite builds and serves
- OIDC Keycloak auth flow configured (backend sessions + HttpOnly cookies)
- Docker compose runs backend, frontend, Keycloak, DB
- Preflight passes (all required files present)

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/core/database.py`, `backend/app/models/__init__.py`, `backend/app/api/routes/health.py`, `backend/app/api/routes/auth.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/Dockerfile`, `compose.yaml`, `.env.example`, `.gitignore`, `portfolio.json`, `README.md`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_database.py`, `frontend/src/__tests__/App.test.tsx`

### plugin-validator — Cursor plugin manifest and component validator

Status: planned

Acceptance:
- Validates plugin.json against schema
- Checks SKILL.md frontmatter parsing
- Verifies agents/, skills/, hooks/, mcp.json paths exist
- Validates mcp.json placeholders against variables
- Detects unlisted plugin directories

### diff-quality-analyzer — Diff rendering quality analyzer (issue #472)

Status: planned

Acceptance:
- Parses raw diff and computes line numbers from hunk headers
- Detects import lines filtered before numbering
- Detects whitespace-only collapsing hiding meaningful changes
- Reports issues with line references

### symlink-detector — Local plugin symlink detection (issue #35)

Status: planned

Acceptance:
- Scans ~/.cursor/plugins/local for symlinks
- Reports symlinked plugins that won't load
- Suggests copy-based workflow

### oauth-scope-auditor — OAuth scope auditor for connectors (issue #385)

Status: planned

Acceptance:
- Checks declared scopes against required API scopes
- Identifies missing scopes (e.g., gmail.settings.basic)
- Generates remediation report

### llm-explanations — Opt-in LLM explanations for validation findings

Status: planned

Acceptance:
- LLM adapter supports OpenAI-compatible, Anthropic, Gemini, Ollama
- Explanations labeled advisory, grounded in actual records
- Clear provider errors, no fabricated responses
- Works without LLM key (deterministic core)

