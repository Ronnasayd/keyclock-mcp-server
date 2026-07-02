# Specs — Propagate OpenAPI summary/description into MCP tools

Source: `docs/plans/sim-crie-um-plano-joyful-tulip.md`. Requirement IDs traceable to tasks.

## 1. Scope

MCP server generates tools straight from `spec/keycloak-openapi.json` operationIds (e.g.
`put_admin_realms_realm`) with no human-readable context. Agent cannot distinguish similarly-named
tools (dozens of `delete_admin_realms_realm_*`). Goal: propagate `summary`/`description` from each
OpenAPI operation and parameter through the parse → generate pipeline into the `MCPTool` exposed to
clients, so `tools/list` responses carry real context.

## 2. Functional Requirements

### FR-1 Operation model carries summary/description

- `Operation` (`src/keycloak_mcp/openapi/models.py`) gains `summary: str | None = None` and
  `description: str | None = None`.
- `Param` gains `description: str | None = None`.

### FR-2 Parser extracts summary/description

- `_parse_operation` (`src/keycloak_mcp/openapi/parser.py`) reads `raw_operation.get("summary")`
  and `raw_operation.get("description")` into `Operation`.
- `_parse_params` reads `raw_param.get("description")` into `Param`.
- Missing fields in the raw spec → `None`, no error.

### FR-3 Tool generator builds a combined description

- `generate_tools()` (`src/keycloak_mcp/tools/generator.py`) computes
  `tool_description = operation.description or operation.summary or None`; when both present,
  concatenate as `f"{summary}\n\n{description}"`.
- `tool_description` passed as `description=` to `GeneratedTool(...)`, which FastMCP's
  `Tool.to_mcp_tool()` surfaces as the real MCP `description` field (default `None` today).

### FR-4 Input schema carries parameter descriptions

- `build_input_schema()` (`src/keycloak_mcp/openapi/validator.py`) merges `param.description` into
  `properties[param.name]["description"]` for each param.
- Do not overwrite an existing `"description"` key already present via `resolve_refs`
  (schema-level description wins over param-level).

## 3. Non-Functional Requirements

- NFR-1: No regression to existing parser/generator/validator test suite (`pytest`).
- NFR-2: Backward compatible — operations without summary/description still generate tools with
  `description=None`, exactly as before.

## 4. Out of Scope

- Rewriting/improving spec content itself (garbage-in stays garbage-in).
- i18n or truncation of long descriptions.
- Response/output schema descriptions.

## 5. Verification

1. `pytest` — full suite green, update fixtures if parser/generator tests assert on `Operation`/
   `GeneratedTool` shape.
2. Parse a real operation from `spec/keycloak-openapi.json` known to have `summary`/`description`
   (e.g. a `users` or `clients` route) — confirm both fields populate on `Operation`.
3. Run `generate_tools()` over the real spec, inspect 2-3 `GeneratedTool.description` — confirm
   non-`None` for operations with spec summary/description.
4. If feasible, boot the MCP server locally and list tools via a client (`mcp dev` / inspector) to
   confirm `description` appears in the `tools/list` response.
