# Design — Keycloak MCP Server (OpenAPI-Driven)

Companion to Specs.md. Covers module boundaries, data flow, key decisions.

## 1. Module Layout

```
src/keycloak_mcp/
├── __init__.py
├── server.py            # FastMCP app bootstrap, tool registration
├── config.py             # pydantic-settings: env → Settings
├── openapi/
│   ├── parser.py         # spec/keycloak-openapi.json -> list[Operation]
│   └── models.py         # Operation, Param, RequestBodySchema dataclasses
├── tools/
│   └── generator.py       # Operation -> registered FastMCP tool (metaprogramming)
├── auth/
│   ├── manager.py         # AuthManager protocol + token acquisition
│   ├── client_credentials.py
│   └── password.py        # ROPC
├── http/
│   └── client.py          # thin httpx.AsyncClient wrapper, no retry
├── validation/
│   └── validator.py       # jsonschema validation of params/body pre-request
└── errors.py              # KeycloakApiError (status + body passthrough)

scripts/
└── sync_openapi.py        # manual re-fetch of official openapi.json

spec/
└── keycloak-openapi.json  # vendored spec

tests/
├── test_parser.py
├── test_generator.py
├── test_auth.py
└── test_errors.py
```

## 2. Data Flow

**Startup:**

1. `config.py` loads `Settings` from env (`pydantic-settings`), validates `AUTH_METHOD` + required conditional fields present.
2. `openapi/parser.py` loads vendored spec once → `list[Operation]` (cached in memory, no reparse per call).
3. `tools/generator.py` iterates operations → for each, builds MCP tool: name = operationId (or synthesized per IR-3), input schema = params + body schema, handler = closure binding operation + shared `HttpClient`/`AuthManager`.
4. `server.py` registers all tools with FastMCP, starts stdio transport.

**Tool call:**

1. Agent invokes tool with args (incl. `realm` if operation requires it).
2. `validation/validator.py` validates args against the operation's JSON schema. Fail → raise validation error immediately, no HTTP call (FR-6).
3. `auth/manager.py` returns current access token. No refresh logic (IR-1) — if Keycloak rejects with 401, that 401 flows through FR-7 unmodified; caller must reauth (new server process or future v1.1 feature).
4. `http/client.py` builds request (method/path/body from operation + resolved path/query params) and calls Keycloak. No retry (IR-2) — network exceptions propagate as-is.
5. Response: 2xx → return parsed body to caller. Non-2xx → raise `KeycloakApiError(status, body)`, MCP layer serializes it back to the agent verbatim (FR-7).

## 3. Key Decisions

- **Metaprogramming approach**: build tools at _startup_, not via decorators per-operation — the operation count (100+) makes static declarations unmaintainable. `generator.py` uses `functools.partial`/closures over a single generic handler rather than `exec`-based codegen, to keep tool functions inspectable and debuggable (avoids the common pitfall of `exec`-generated functions being opaque in stack traces).
- **Schema-driven input validation**: reuse the OpenAPI JSON schema fragments directly with `jsonschema` rather than round-tripping through Pydantic model codegen — avoids an extra build step (`datamodel-code-generator`) for MVP; revisit if type-safety needs grow.
- **AuthManager as a Protocol** with two implementations (`client_credentials`, `password`) selected at startup by `Settings.auth_method` — no runtime switching, no factory pattern needed beyond a single `if/match` in `config.py` or `server.py` bootstrap.
- **No retry, no refresh**: both IR-1 and IR-2 are deliberate simplicity choices (see PRD rationale) — do not add resilience logic without a new requirement.
- **Failure isolation during generation**: a single malformed operation must not abort tool generation. `generator.py` wraps per-operation build in try/except, logs+skips, and exposes a `generation_report` (succeeded/failed operationIds) for startup logging — mitigates PRD §11 "silent failure" risk.

## 4. Open Questions / Deferred

- Exact library for OpenAPI parsing (`openapi-core` vs custom) — decide during FR-1 implementation, prototype both against 2-3 representative operations from the real spec before committing.
- Tool volume (100+) may need agent-side filtering — explicitly deferred to phase 2 per PRD §11, not part of this design.
