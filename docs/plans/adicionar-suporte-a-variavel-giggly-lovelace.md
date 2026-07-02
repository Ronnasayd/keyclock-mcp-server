# Add MCP_KEYCLOAK_READ_ONLY support

## Context

User wants a `MCP_KEYCLOAK_READ_ONLY` env var. When set (true), only GET
(read-only) Keycloak operations should be exposed as MCP tools; non-GET
(POST/PUT/DELETE — writes) operations must be blocked.

## Approach

Filter at tool-generation time, not at request time. If a write tool is never
registered with FastMCP, the LLM client never sees it as callable — cleaner
than exposing it and rejecting at call time.

### Files to change

**`src/keycloak_mcp/config.py`**

- Add field: `read_only: bool = False` (auto env `MCP_KEYCLOAK_READ_ONLY`,
  pydantic-settings parses `"true"/"1"/"false"/"0"` natively — no custom
  parsing needed).

**`src/keycloak_mcp/tools/generator.py`**

- `generate_tools(...)` gains a `read_only: bool = False` param.
- Inside the loop (line 84-102 today), when `read_only` is true and
  `operation.method.upper() != "GET"`, skip registering the tool — log it and
  record it in the report (add `GenerationReport.blocked: list[str]` alongside
  existing `succeeded`/`failed`, so callers/logs can see what was hidden).

**`src/keycloak_mcp/server.py`**

- `build_server()` passes `read_only=settings.read_only` into
  `generate_tools(...)` (line 45-50).

### Verification

- Run existing test suite (`pytest`) after adding a unit test in
  `tests/` mirroring existing generator tests: build `generate_tools` with
  `read_only=True` over a mix of GET/POST operations, assert only GET tool
  names appear in the returned tools list and non-GET ones land in
  `report.blocked`.
- Manually: set `MCP_KEYCLOAK_READ_ONLY=true`, run server, list tools via
  MCP client, confirm only read (`get_*`) tools are present.

### Docs

- Update `README.md` env var table (lines ~21-27) adding
  `MCP_KEYCLOAK_READ_ONLY` row (optional, default `false`, boolean — restricts
  server to GET-only operations).
