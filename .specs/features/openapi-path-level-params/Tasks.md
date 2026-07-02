# Tasks — Fix path-level OpenAPI params dropped

Atomic tasks derived from Design.md + Specs.md. `[P]` = parallelizable within its wave.
Gate = command that must pass before task considered done.

## Wave 0 — Parser fix (no deps)

- **T0.1** `openapi/parser.py::parse_spec`: extract `path_item.get("parameters", [])` per
  `path, path_item` pair, pass as new `path_level_params` arg into `_parse_operation` (FR-1).
- **T0.2** `openapi/parser.py::_parse_operation`: accept `path_level_params: list[dict]`; merge
  with `raw_operation.get("parameters", [])` keyed by `(name, in)`, operation-level wins on
  collision; pass merged list to `_parse_params` (FR-2).
  - Depends on: T0.1 (same function signature change, do together in one edit).
  - Tests: path item with shared `parameters` + `get` with no operation-level params → merged
    `Operation.params` contains shared param, `required=True`; path item with shared param +
    operation declaring same `(name, in)` differently → operation-level wins; path item with no
    shared `parameters` → behavior unchanged (NFR-3).
  - Gate: `pytest tests/test_parser.py`

## Wave 1 — Verification (depends: Wave 0)

- **T1.1** Full suite: `pytest` — confirm no regressions (NFR-1).
- **T1.2** Parse real spec: assert `get_admin_realms_realm` operation (from
  `spec/keycloak-openapi.json`) now has `realm` in `Operation.params`, `required=True`.
- **T1.3** Manual: invoke `mcp__keycloak__get_admin_realms_realm` with `{"realm": "lingopass"}`
  → returns realm data; omit `realm` → clean `InputValidationError`, not bare `KeyError`.

## Dependency Summary

```
T0.1 ─> T0.2 ─> T1.1 ─> T1.2 ─> T1.3
```

## Notes

- 1-file change (`parser.py`), no new modules — matches Design §1 scope exactly. Do not
  introduce abstractions beyond what's listed here.
