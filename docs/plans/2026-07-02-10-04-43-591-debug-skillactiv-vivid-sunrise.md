# Fix: path-level OpenAPI params dropped, causing bare KeyError('realm')

## Context

Calling MCP tool `get_admin_realms_realm` (GET `/admin/realms/{realm}`) with
`{}` or even `{"realm": "lingopass"}` fails with a bare `KeyError: 'realm'`
instead of returning the realm or a clean validation error. Root cause traced
via log lines 1246-1268 (`/tmp/hooks.log`): the tool schema for this
operation exposes zero properties, so any input (including omitting `realm`)
passes JSON-schema validation, and the request builder then fails formatting
the URL path.

The underlying bug: OpenAPI 3.0 lets a path item declare `parameters` once,
shared by all HTTP methods under that path, instead of repeating them per
operation. `keycloak-openapi.json`'s `/admin/realms/{realm}` entry does
exactly this — `realm` is declared as a sibling of `get`/`put`/`delete`, not
inside `get` itself:

```json
"/admin/realms/{realm}" : {
  "get" : { ... no "parameters" key ... },
  "put" : { ... },
  "delete" : { ... },
  "parameters" : [ { "name": "realm", "in": "path", "required": true, ... } ]
}
```

`src/keycloak_mcp/openapi/parser.py::parse_spec` only reads
`raw_operation.get("parameters", [])` (operation-level) when building each
`Operation`, never `path_item.get("parameters", [])`. Result: `Operation.params`
is empty for every method on this path. This empties out every downstream
consumer:

- `validation/validator.py::build_input_schema` — generates a tool schema
  with no `realm` property/requirement, so `{}` passes validation.
- `openapi/realm.py::resolve_realm` — finds no `realm` param, so the
  default-realm fallback never triggers either.
- `tools/generator.py::GeneratedTool.run` — builds `path_params = {}`.
- `http/client.py:27` — `operation.path.format(**path_params)` raises
  `KeyError: 'realm'` unhandled (only `KeycloakApiError` is caught in
  `run()`).

This is likely not limited to `/admin/realms/{realm}` — any path in the spec
that declares shared parameters at the path-item level instead of per-
operation will have the same silent parameter loss.

## Fix

In `src/keycloak_mcp/openapi/parser.py`:

- In `parse_spec`, for each `path, path_item` pair, extract
  `path_item.get("parameters", [])` once before iterating methods.
- Pass these shared params into `_parse_operation` (new parameter, e.g.
  `path_level_params`).
- In `_parse_operation`, merge `path_level_params` with
  `raw_operation.get("parameters", [])` before calling `_parse_params`:
  operation-level entries override path-level entries with the same
  `(name, in)` key, per OpenAPI parameter inheritance rules. Path items are
  dicts (not lists), so `HTTP_METHODS` iteration in `parse_spec` already
  skips the `"parameters"` key safely — no change needed there beyond
  reading it out.

No other files need to change — `_parse_params`, `build_input_schema`,
`resolve_realm`, and `GeneratedTool.run` all already work correctly once
`Operation.params` is populated correctly.

## Verification

1. Re-run the parser against `spec/keycloak-openapi.json` (unit test or a
   quick script) and assert that the `Operation` for
   `get_admin_realms_realm` now has a `params` list containing a `realm`
   path param with `required=True`.
2. Check existing/adjacent test suite for parser tests (likely
   `tests/openapi/test_parser.py` or similar) — add a case using a path item
   with shared `parameters` and per-operation-only `parameters`, verifying
   correct merge/override behavior.
3. Manually invoke `mcp__keycloak__get_admin_realms_realm` with
   `{"realm": "lingopass"}` and confirm it now returns realm data instead of
   `KeyError: 'realm'`; also confirm omitting `realm` now produces a clean
   `InputValidationError` (missing required field) rather than a bare
   `KeyError`.
