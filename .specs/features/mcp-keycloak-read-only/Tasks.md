# MCP_KEYCLOCK_READ_ONLY Tasks

**Design**: `.specs/features/mcp-keycloak-read-only/Design.md`
**Status**: Draft

---

## Execution Plan

### Phase 1: Config + Report shape (Sequential)

```
T1 → T2
```

### Phase 2: Generation + Wiring (Sequential, depends on Phase 1)

```
T2 → T3 → T4
```

### Phase 3: Tests + Docs (Sequential, depends on Phase 2)

```
T4 → T5 → T6
```

### Diagram-Definition Cross-Check

| Task | Depends on | Matches diagram? |
| ---- | ---------- | ---------------- |
| T1   | -          | ✅               |
| T2   | T1         | ✅               |
| T3   | T2         | ✅               |
| T4   | T3         | ✅               |
| T5   | T4         | ✅               |
| T6   | T4         | ✅               |

---

## Task Breakdown

### T1: Add `read_only` field to `Settings`

- **What**: Add `read_only: bool = False` to `Settings` in `src/keycloak_mcp/config.py`.
- **Where**: `src/keycloak_mcp/config.py`
- **Depends on**: -
- **Reuses**: existing `SettingsConfigDict(env_prefix="MCP_KEYCLOCK_")` — no custom parsing needed.
- **Done when**: `Settings(read_only=True)` and env `MCP_KEYCLOCK_READ_ONLY=true` both yield `True`.
- **Tests**: none (trivial pydantic field; covered indirectly by T5).
- **Gate**: `uv run mypy src/keycloak_mcp/config.py` (or project's type-check command) passes.

### T2: Add `blocked` field to `GenerationReport`

- **What**: Add `blocked: list[str] = field(default_factory=list)` to `GenerationReport` in `src/keycloak_mcp/tools/generator.py`.
- **Where**: `src/keycloak_mcp/tools/generator.py`
- **Depends on**: T1 (none functionally, ordered for logical flow)
- **Reuses**: existing `succeeded`/`failed` dataclass field pattern.
- **Done when**: `GenerationReport().blocked == []`.
- **Tests**: none standalone (covered by T5).
- **Gate**: import/compile check.

### T3: Filter non-GET operations in `generate_tools`

- **What**: Add `read_only: bool = False` param to `generate_tools`; inside the loop, when `read_only and operation.method.upper() != "GET"`, append `operation.operation_id` to `report.blocked` and skip tool creation (do not append to `tools`).
- **Where**: `src/keycloak_mcp/tools/generator.py:75-104`
- **Depends on**: T2
- **Reuses**: existing per-operation loop and `try/except` structure.
- **Done when**: with `read_only=True`, only GET-method operations appear in returned `tools`; all others land in `report.blocked`, not `report.succeeded`/`report.failed`.
- **Tests**: unit test (see T5).
- **Gate**: full test gate for this module.

### T4: Wire `settings.read_only` into `build_server`

- **What**: Pass `read_only=settings.read_only` into the `generate_tools(...)` call in `build_server`.
- **Where**: `src/keycloak_mcp/server.py:45-50`
- **Depends on**: T3
- **Reuses**: existing `build_server` signature (no change).
- **Done when**: `build_server(settings)` with `settings.read_only=True` produces an `FastMCP` instance whose tool list excludes non-GET operations.
- **Tests**: covered by T5 (generator-level) — no separate server test required unless project convention demands one.
- **Gate**: full test gate.

### T5: Unit test for read-only filtering

- **What**: Add test in `tests/` (mirroring existing generator tests) that builds `generate_tools` with `read_only=True` over a mix of GET/POST operations, asserts only GET tool names appear in the returned `tools` list and non-GET operation ids land in `report.blocked`. Also assert default (`read_only=False`) behavior is unchanged.
- **Where**: `tests/` (co-located with existing `tools/generator` tests — match existing test file naming)
- **Depends on**: T4
- **Reuses**: existing test fixtures/operation builders for generator tests.
- **Done when**: new tests pass; full suite (`pytest`) green.
- **Tests**: this task IS the test.
- **Gate**: `pytest` full run passes.

### T6: Document `MCP_KEYCLOCK_READ_ONLY` in README

- **What**: Add a row to the env var table (README.md, near lines 15-27) for `MCP_KEYCLOCK_READ_ONLY` — optional, default `false`, boolean, restricts server to GET-only operations.
- **Where**: `README.md`
- **Depends on**: T4
- **Reuses**: existing table format.
- **Done when**: table includes the new row with correct default/description.
- **Tests**: none (docs).
- **Gate**: manual read-through.

---

## Test Co-location Validation

| Task | Creates/modifies     | Test type required | Included in task? |
| ---- | -------------------- | ------------------ | ----------------- |
| T1   | config field         | none (trivial)     | N/A               |
| T2   | dataclass field      | none (trivial)     | N/A               |
| T3   | core filtering logic | unit               | ✅ via T5         |
| T4   | wiring               | unit (indirect)    | ✅ via T5         |
| T5   | test file            | is the test        | ✅                |
| T6   | docs                 | none               | N/A               |

No `TESTING.md` found in `.specs/codebase/` — using project's existing test pattern
(`pytest`, tests mirroring generator module) as the baseline convention per T5.
