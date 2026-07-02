# Design — Propagate OpenAPI summary/description into MCP tools

Companion to Specs.md. Small, surgical change — 4 files, no new modules.

## 1. Pipeline (gap → fix)

```
spec/keycloak-openapi.json
        │  (summary, description on operation + params)
        ▼
openapi/parser.py  _parse_operation / _parse_params   [FR-2: now reads summary/description]
        │
        ▼
openapi/models.py  Operation / Param                   [FR-1: now has summary/description fields]
        │
        ├──> tools/generator.py  generate_tools()       [FR-3: builds tool_description, passes to GeneratedTool]
        │           │
        │           ▼
        │     GeneratedTool(description=...) ──> fastmcp Tool.to_mcp_tool() ──> MCPTool.description
        │
        └──> openapi/validator.py  build_input_schema() [FR-4: merges param.description into JSON schema properties]
```

No new files. Touches exactly the 4 files identified in the plan:

- `src/keycloak_mcp/openapi/models.py`
- `src/keycloak_mcp/openapi/parser.py`
- `src/keycloak_mcp/tools/generator.py`
- `src/keycloak_mcp/openapi/validator.py`

## 2. Key Decisions

- **Description precedence**: `operation.description or operation.summary or None`. When both
  exist, concatenate `f"{summary}\n\n{description}"` — summary as short title, description as
  body. Keeps a single deterministic rule instead of per-operation heuristics.
- **Param schema description**: merge `param.description` into the schema dict without
  overwriting an existing `"description"` key from `resolve_refs` — schema-level (post-$ref
  resolution) descriptions are considered more authoritative than the OpenAPI param-level one,
  since $ref schemas may carry richer domain descriptions.
- **No new dataclasses/abstractions**: fields added directly to existing `Operation`/`Param`
  dataclasses as optional (`str | None = None`) — fully backward compatible, no migration needed
  for existing callers/tests that construct these without the new fields.
- **Library dependency**: none — plain dict `.get()` reads, no schema library changes.

## 3. Open Questions / Deferred

- None — plan is unambiguous, scope is fixed at 4 files per Specs §1.
