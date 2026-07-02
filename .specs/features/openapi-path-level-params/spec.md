# Specs — Fix path-level OpenAPI params dropped (bare KeyError('realm'))

Source: `docs/plans/2026-07-02-10-04-43-591-debug-skillactiv-vivid-sunrise.md`. Requirement IDs
traceable to tasks.

## 1. Scope

`get_admin_realms_realm` (GET `/admin/realms/{realm}`) tool schema exposes zero properties, so
`{}` passes validation and `http/client.py:27` raises unhandled `KeyError: 'realm'`. Root cause:
OpenAPI 3.0 path items may declare `parameters` once as a sibling of the HTTP methods (shared
across `get`/`put`/`delete`), instead of repeating them per operation. `parser.py::parse_spec`
only reads operation-level `parameters`, never path-item-level, so `Operation.params` is empty
for every method on any path using this pattern. Goal: merge path-level params into each
operation so schema generation, realm resolution, and path formatting see the full param set.

## 2. Functional Requirements

### FR-1 Parser extracts path-item-level parameters

- `parse_spec` (`src/keycloak_mcp/openapi/parser.py`) reads `path_item.get("parameters", [])`
  once per `path, path_item` pair, before iterating methods.

### FR-2 Path-level params merge into each operation, operation-level wins on conflict

- `_parse_operation` gains a `path_level_params: list[dict]` parameter.
- Before calling `_parse_params`, merge `path_level_params` with
  `raw_operation.get("parameters", [])`: keyed by `(name, in)`; an operation-level entry with the
  same key overrides the path-level entry (per OpenAPI parameter inheritance rules).
- Merged list passed to `_parse_params` unchanged otherwise.

## 3. Non-Functional Requirements

- NFR-1: No regression to existing parser test suite (`pytest`).
- NFR-2: `HTTP_METHODS` iteration in `parse_spec` already skips the `"parameters"` key on
  `path_item` (it's not in `HTTP_METHODS`) — no change needed there beyond reading it out.
- NFR-3: Backward compatible — paths without path-item-level `parameters` behave exactly as
  before (empty merge input, no-op).

## 4. Out of Scope

- Changes to `_parse_params`, `build_input_schema`, `resolve_realm`, `GeneratedTool.run` — all
  already correct once `Operation.params` is populated.
- Broader error handling for unhandled path-formatting `KeyError` in `http/client.py:27` (bug is
  fixed at the root — empty schema no longer lets `{}` pass validation).

## 5. Verification

1. `pytest` — full suite green.
2. Parser test: path item with shared `parameters` (e.g. `realm`) and a `get` with no
   operation-level `parameters` → resulting `Operation.params` contains the shared param,
   `required=True`.
3. Parser test: path item with shared `parameters` plus an operation declaring the same
   `(name, in)` with different attributes → operation-level entry wins.
4. Re-run parser against `spec/keycloak-openapi.json`, assert `get_admin_realms_realm` operation
   now has a `realm` path param, `required=True`.
5. Manually invoke `mcp__keycloak__get_admin_realms_realm` with `{"realm": "lingopass"}` →
   returns realm data instead of `KeyError: 'realm'`; omitting `realm` → clean
   `InputValidationError` (missing required field), not a bare `KeyError`.
