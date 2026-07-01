# Specs — Keycloak MCP Server (OpenAPI-Driven)

Source: PRD.md. Requirement IDs traceable to implementation tasks.

## 1. Scope

MCP server (Python/FastMCP) exposing Keycloak Admin REST API as MCP tools, generated via
metaprogramming from vendored `openapi.json`. One tool per `operationId`. Input validated
against OpenAPI schema before HTTP call. Errors passed through structured (status + body).

## 2. Functional Requirements

### FR-1 OpenAPI Parser

- Parse vendored `spec/keycloak-openapi.json`.
- Extract per-operation: path, method, operationId, params (path/query/header), request body schema, response schema (parsed but not validated — output validation out of scope).
- IR-3: if `operationId` missing, synthesize `{method}_{path_slug}`, log warning.

### FR-2 Tool Generator (metaprogramming)

- 1 MCP tool per operation (real or synthesized operationId).
- Tool name/input schema derived automatically from parsed operation.
- Failing operations (malformed schema) must not crash generation — skip + log, don't silently drop without trace (Risk in PRD §11).

### FR-3 HTTP Client

- Generic async client (`httpx`) for Admin REST API.
- Base URL from `KEYCLOAK_BASE_URL` env.
- No retry on network failure (IR-2) — failure surfaces directly to caller.

### FR-4 Auth Manager

- Configurable method via `AUTH_METHOD` env: `client_credentials` | `password` (ROPC).
- `client_credentials`: `CLIENT_ID` + `CLIENT_SECRET`.
- `password`: `ADMIN_USERNAME` + `ADMIN_PASSWORD` (+ `CLIENT_ID`).
- No automatic token refresh, proactive or reactive (IR-1). Expired token → error surfaces, caller must reauthenticate.

### FR-5 Multi-realm support

- `realm` param required/optional per-endpoint per OpenAPI path definition.
- No multi-tenant credentials (1 credential set per server instance).

### FR-6 Input Validation

- Validate params + body against OpenAPI schema before dispatching HTTP request.
- Validation failure → structured error to caller, no HTTP round-trip.

### FR-7 Error Handling

- All Keycloak HTTP errors (incl. 403) passed through raw: status code + original body (IR-5).
- No conditional logic per status code, no custom messages.

### FR-8 Logging

- INFO/ERROR level, structured JSON (per AGENTS.md logging convention).
- Log: method, path, status. Never log body, tokens, passwords, or other PII.

### FR-9 Spec Sync Script

- `scripts/sync_openapi.py`: re-fetch `openapi.json` from official URL, overwrite vendored copy.
- Manual invocation only — no runtime fetch (Out of Scope).

### FR-10 Distribution

- Runnable via `uvx keycloak-mcp-server` (IR-6). No Docker/container in MVP.

## 3. Non-Functional Requirements

- NFR-1: Startup (spec parse + tool generation) < 2s for full spec.
- NFR-2: Test coverage > 80% for generator + auth manager modules.
- NFR-3: 100% of parseable OpenAPI operations produce a tool.
- NFR-4: No secrets/PII in logs — enforced in code review, not just convention.

## 4. Out of Scope (MVP)

- Web admin/monitoring panel.
- Output/response schema validation.
- Tool grouping by resource (stays 1:1 with operationId).
- Runtime auto-fetch of openapi.json.
- Multi-tenant credentials.
- Automatic token refresh (IR-1).
- Automatic retry on network failure (IR-2).
- External secret manager integration (IR-4).
- Docker packaging / shared SSE server (IR-6).

## 5. Config Surface

| Var                 | Required    | Notes                              |
| ------------------- | ----------- | ---------------------------------- |
| `KEYCLOAK_BASE_URL` | yes         | Admin API base URL                 |
| `AUTH_METHOD`       | yes         | `client_credentials` \| `password` |
| `CLIENT_ID`         | conditional | both auth methods                  |
| `CLIENT_SECRET`     | conditional | `client_credentials` only          |
| `ADMIN_USERNAME`    | conditional | `password` only                    |
| `ADMIN_PASSWORD`    | conditional | `password` only                    |
| `DEFAULT_REALM`     | no          | fallback realm if tool omits it    |

## 6. KPIs (from PRD §9)

- % operations covered by generated tool (target 100%).
- Validation-error catch rate pre-request.
- Startup time (<2s target).
- Test coverage (>80% target, generator + auth manager).
