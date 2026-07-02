# Design — Fix path-level OpenAPI params dropped

Companion to Specs.md. Small, surgical change — 1 file, no new modules.

## 1. Pipeline (gap → fix)

```
spec/keycloak-openapi.json
   "/admin/realms/{realm}": { get: {...}, put: {...}, delete: {...},
                               parameters: [ {name: realm, in: path, required: true} ] }
        │
        ▼
openapi/parser.py  parse_spec()          [FR-1: now also reads path_item.get("parameters", [])]
        │  path_level_params
        ▼
openapi/parser.py  _parse_operation()    [FR-2: merges path_level_params + operation-level params,
        │                                        operation-level wins on (name, in) collision]
        ▼
openapi/models.py  Operation.params      (already correct — no changes needed downstream)
        │
        ├──> validation/validator.py::build_input_schema   (already correct)
        ├──> openapi/realm.py::resolve_realm                (already correct)
        └──> tools/generator.py::GeneratedTool.run           (already correct)
```

Touches exactly 1 file: `src/keycloak_mcp/openapi/parser.py`.

## 2. Key Decisions

- **Merge, not concatenate**: dedupe by `(name, in)` key so path-level and operation-level
  entries for the same param don't both land in the final list (would break schema `required`
  counts / produce duplicate properties). Operation-level overrides on collision, per OpenAPI
  3.0 parameter-inheritance semantics.
- **Merge point**: inside `_parse_operation`, right before the existing
  `_parse_params(raw_operation.get("parameters", []), spec)` call — smallest possible diff,
  `_parse_params` itself stays untouched (still just maps a flat list of raw param dicts).
- **Extraction point**: `parse_spec` reads `path_item.get("parameters", [])` once per path,
  passes it into every `_parse_operation` call for that path — avoids re-reading it per method.
- **No new dataclass/field**: path-level params are plain `dict`s exactly like operation-level
  ones; merge happens before `Param` construction, so `models.py` needs no changes.

## 3. Open Questions / Deferred

- None — plan is unambiguous, root cause and fix location fully diagnosed already.
