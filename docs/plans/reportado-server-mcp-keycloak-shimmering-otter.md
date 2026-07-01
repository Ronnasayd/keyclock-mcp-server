# Fix: unresolved `$ref` in MCP tool input schemas (e.g. `put_admin_realms_realm`)

## Context

Reported bug: `put_admin_realms_realm` (and every other operation whose request
body is `{"$ref": "#/components/schemas/X"}`) exposes a broken `inputSchema.body`
to MCP clients — a bare `$ref` pointer with no `components` alongside it, so
clients/validators see `PointerToNowhere`. Confirmed via investigation
(`src/keycloak_mcp/openapi/parser.py::_parse_request_body`,
`src/keycloak_mcp/validation/validator.py::build_input_schema`): the spec
(`src/keycloak_mcp/spec/keycloak-openapi.json`) is loaded whole but `$ref`
pointers are never resolved against `components.schemas` — they're passed
through verbatim into both the generated `Tool.inputSchema` and the
`jsonschema.Draft7Validator` used in `validate_input`. `RealmRepresentation`
itself is present in the bundled spec — this is not a missing-component issue,
it's a missing-dereference issue. Root cause affects every ref-typed request
body and param schema across all ~370 generated tools, not just realm update.

## Approach

Resolve `$ref` pointers by inlining them at spec-parse time, before
`Operation` objects are built, so `RequestBodySchema.schema` and
`Param.schema` are always fully self-contained (no `$ref` left unresolved).

1. **New resolver module** `src/keycloak_mcp/openapi/deref.py`:
   - `resolve_refs(schema: Any, root: dict, seen: frozenset[str] = frozenset()) -> Any`
   - Recursively walks dict/list nodes. When it hits `{"$ref": "#/components/schemas/X"}`,
     looks up `root["components"]["schemas"]["X"]`, and recurses into a copy of
     that resolved schema.
   - Cycle protection: track ref pointers already being resolved in the current
     path (`seen`); if a `$ref` re-enters itself (Keycloak schemas do have
     self-referential structures, e.g. `RoleRepresentation.composites`), stop
     inlining further and leave `{"$ref": ...}` **plus** a top level `$defs`
     bundle as fallback — simplest correct option: keep inlining but cut
     recursion at the cycle point by substituting `true` (permissive/any-schema)
     for the repeated ref, so the resulting schema stays valid JSON Schema
     without infinite expansion.
   - Must not mutate the original spec dict (copy schemas before merging
     sibling keys like `description` that coexist with `$ref` in OpenAPI 3.1).

2. **Wire into parsing** — `src/keycloak_mcp/openapi/parser.py`:
   - `parse_spec(spec)` already has the full `spec` dict (with `components`)
     in scope. Pass `spec` down into `_parse_operation` → `_parse_params` /
     `_parse_request_body`, and call `resolve_refs(raw_schema, spec)` when
     building `Param.schema` and `RequestBodySchema.schema`.

3. **No changes needed** in `validator.py` or `generator.py` — once
   `Operation.request_body.schema` / `Param.schema` are pre-resolved,
   `build_input_schema` and `validate_input` work unchanged (they just consume
   whatever schema dict is on the `Operation`).

4. **Tests**: add a unit test for `resolve_refs` (simple ref, nested ref,
   self-referential cycle) and a parser-level test asserting
   `put_admin_realms_realm`'s generated `body` schema has no `$ref` key and
   contains expected `RealmRepresentation` properties (e.g.
   `accessTokenLifespan`). Check `tests/` directory structure first to match
   existing conventions before adding files.

## Verification

- Run existing test suite (`pytest` — check `pyproject.toml`/`AGENTS.md` for
  the exact invocation) to confirm no regressions.
- Add/run the new deref + parser tests above.
- Manually invoke `load_operations()` for `put_admin_realms_realm` and assert
  `operation.request_body.schema` contains no `"$ref"` anywhere (recursive
  check) and includes `accessTokenLifespan` in `properties`.
- If feasible, start the MCP server and call `put_admin_realms_realm` via the
  `mcp__keycloak__put_admin_realms_realm` tool already connected in this
  session against a real/test Keycloak instance to confirm the update
  succeeds end-to-end (no `PointerToNowhere`).
