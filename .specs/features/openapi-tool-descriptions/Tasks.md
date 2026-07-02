# Tasks — Propagate OpenAPI summary/description into MCP tools

Atomic tasks derived from Design.md + Specs.md. `[P]` = parallelizable within its wave.
Gate = command that must pass before task considered done.

## Wave 0 — Models (no deps)

- **T0.1** `openapi/models.py`: add `summary: str | None = None`, `description: str | None = None`
  to `Operation`; add `description: str | None = None` to `Param`.
  - Done when: module imports, existing construction call sites still work (optional fields).

## Wave 1 — Parser & Validator (depends: T0.1)

- **T1.1** [P] `openapi/parser.py`: `_parse_operation` reads `raw_operation.get("summary")` /
  `.get("description")` into `Operation` (FR-2).
  - Tests: fixture operation with both fields → `Operation.summary`/`.description` populated;
    fixture operation with neither → both `None`.
- **T1.2** [P] `openapi/parser.py`: `_parse_params` reads `raw_param.get("description")` into
  `Param` (FR-2).
  - Tests: fixture param with description → populated; without → `None`.
  - Gate: `pytest tests/test_parser.py` (or wherever parser tests live)
- **T1.3** [P] `openapi/validator.py`: `build_input_schema()` merges `param.description` into
  `properties[param.name]["description"]`, skip if schema already has `"description"` (FR-4).
  - Tests: param with description + no existing schema description → merged in; schema already
    has `"description"` from `resolve_refs` → untouched (param description does not overwrite).
  - Gate: `pytest tests/test_validator.py` (or wherever validator tests live)

## Wave 2 — Generator (depends: T0.1, T1.1)

- **T2.1** `tools/generator.py`: `generate_tools()` computes `tool_description =
operation.description or operation.summary or None`, concatenating
  `f"{summary}\n\n{description}"` when both present; pass `description=tool_description` to
  `GeneratedTool(...)` (FR-3).
  - Tests: operation with summary only → description = summary; with description only →
    description = description; with both → concatenated `f"{summary}\n\n{description}"`; with
    neither → `None`.
  - Gate: `pytest tests/test_generator.py`

## Wave 3 — Verification (depends: Wave 2)

- **T3.1** Full suite: `pytest` — confirm no regressions (NFR-1).
- **T3.2** Manual check against real spec: parse `spec/keycloak-openapi.json`, pick 2-3 operations
  known to carry summary/description (users/clients routes), confirm `Operation` fields populate
  and `generate_tools()` output has non-`None` `description`.
- **T3.3** Optional: boot MCP server locally, list tools via client/inspector, confirm
  `description` shows in `tools/list` response (Specs §5.4).

## Dependency Summary

```
T0.1 ─┬─> T1.1 ─┬─> T2.1 ─> T3.1 ─> T3.2 ─> T3.3
      ├─> T1.2 ─┘
      └─> T1.3
```

## Notes

- 4-file change, no new modules — matches Design §1 scope exactly. Do not introduce abstractions
  beyond what's listed here.
