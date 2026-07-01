# Tasks — Keycloak MCP Server (OpenAPI-Driven)

Atomic tasks derived from Design.md + Specs.md. `[P]` = parallelizable within its wave.
Gate = command that must pass before task considered done.

## Wave 0 — Bootstrap

- **T0.1** Scaffold project: `pyproject.toml` (Python 3.11+), package `src/keycloak_mcp/`, `tests/`, deps (`fastmcp`, `httpx`, `jsonschema`, `pydantic-settings`, `pytest`, `pytest-asyncio`, `respx`).
  - Done when: `uv sync` / `pip install -e .` succeeds, `pytest` runs (0 tests, no errors).
- **T0.2** [P] Vendor `spec/keycloak-openapi.json` — fetch official spec once, commit.
  - Done when: file exists, valid JSON, `openapi` field present.
- **T0.3** [P] `scripts/sync_openapi.py` — fetch URL, overwrite vendored spec (FR-9).
  - Done when: `python scripts/sync_openapi.py --dry-run` diffs without writing; real run updates file.

## Wave 1 — Config & Parser (depends: T0.1)

- **T1.1** `config.py`: `Settings` (pydantic-settings) — `KEYCLOAK_BASE_URL`, `AUTH_METHOD`, conditional fields per FR-4/Specs §5. Validate conditional-required fields at load (FR-4).
  - Tests: missing `CLIENT_SECRET` under `client_credentials` raises; valid password-mode config loads.
  - Gate: `pytest tests/test_config.py`
- **T1.2** `openapi/models.py`: `Operation`, `Param`, dataclasses per Design §1.
  - Done when: importable, no logic yet.
- **T1.3** `openapi/parser.py`: parse spec → `list[Operation]` (FR-1). Implement IR-3 synthesized operationId + warning log.
  - Tests: fixture spec with named + unnamed operationId; malformed operation doesn't crash parse.
  - Gate: `pytest tests/test_parser.py`

## Wave 2 — Auth & HTTP (depends: T1.1)

- **T2.1** [P] `auth/manager.py` — `AuthManager` Protocol.
- **T2.2** [P] `auth/client_credentials.py` — client_credentials grant token fetch.
  - Tests: mocked token endpoint (respx) → token returned; no refresh logic present (assert absence).
- **T2.3** [P] `auth/password.py` — ROPC grant token fetch.
  - Tests: mocked token endpoint → token returned.
  - Gate: `pytest tests/test_auth.py`
- **T2.4** `http/client.py` — async httpx wrapper, builds request from `Operation` + resolved params, no retry (IR-2).
  - Tests: network exception propagates unmodified (no retry attempted — assert call count == 1).
- **T2.5** `errors.py` — `KeycloakApiError(status, body)`, raised on non-2xx, no per-status branching (FR-7/IR-5).
  - Tests: 403 and 500 both produce raw passthrough, no message rewriting.
  - Gate: `pytest tests/test_errors.py`

## Wave 3 — Validation & Generation (depends: T1.3, T2.4, T2.5)

- **T3.1** `validation/validator.py` — jsonschema validation of tool input against operation schema (FR-6).
  - Tests: invalid input rejected pre-request (assert HTTP client never called).
- **T3.2** `tools/generator.py` — build one FastMCP tool per `Operation`: name, input schema, handler (validate → auth → http → error-wrap). Try/except isolation per operation (Design §3).
  - Tests: fixture spec (5-10 ops incl. one malformed) → correct tool count generated, malformed op skipped+logged, generation_report accurate.
  - Gate: `pytest tests/test_generator.py`
- **T3.3** Realm param handling — `realm` required/optional derived from operation path/params (FR-5), `DEFAULT_REALM` fallback when optional and omitted.
  - Tests: operation with required realm rejects missing realm; optional realm falls back to `DEFAULT_REALM`.

## Wave 4 — Server & Logging (depends: Wave 3)

- **T4.1** `server.py` — FastMCP app: load settings, parse spec once, generate+register tools, start stdio transport.
  - Tests: startup with fixture spec registers expected tool count; startup time assertion against NFR-1 (<2s) using real vendored spec.
- **T4.2** Structured JSON logging (FR-8) — method/path/status only, explicit test that body/token never appear in log output.
  - Tests: log capture assert no PII/secret substrings present across a sample of calls.

## Wave 5 — Packaging & Docs (depends: Wave 4)

- **T5.1** `uvx` entry point (IR-6) — `[project.scripts]` in `pyproject.toml`.
  - Done when: `uvx --from . keycloak-mcp-server` boots server.
- **T5.2** README: config vars, `.env` warning (IR-4 — never commit secrets), auth method setup, sync script usage.
- **T5.3** Full coverage check against NFR-2 (>80% generator + auth manager) — `pytest --cov=keycloak_mcp.tools.generator --cov=keycloak_mcp.auth`.
- **T5.4** End-to-end smoke: run server against a local/dev Keycloak instance (if available), invoke 2-3 real tools (list realms, create/delete test user), confirm error passthrough on a deliberate 403.

## Dependency Summary

```
T0.1 ─┬─> T1.1 ─┬─> T2.1,T2.2,T2.3 ─┐
      │         │                    ├─> T3.1,T3.2,T3.3 ─> T4.1,T4.2 ─> T5.*
      └─> T1.2 ─> T1.3 ─────────────┘
                  T2.4,T2.5 ─────────┘
T0.2, T0.3 [P, independent]
```

## Notes

- No task implements token refresh or retry — those are explicitly deferred (IR-1, IR-2). Do not add without a new requirement in Specs.md.
- Skip output/response schema validation entirely (Out of Scope, Specs §4).
