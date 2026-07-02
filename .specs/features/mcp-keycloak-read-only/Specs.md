# MCP_KEYCLOAK_READ_ONLY Support Specification

## Problem Statement

Some MCP clients should only ever read Keycloak state, never mutate it. Today every
generated tool (GET/POST/PUT/DELETE) is exposed regardless of caller intent. Operators
need a way to run the server in a hard read-only mode so write-capable tools are never
even offered to the LLM client.

## Goals

- [ ] Add `MCP_KEYCLOAK_READ_ONLY` env var (boolean, default `false`).
- [ ] When true, only GET operations become MCP tools; non-GET operations are filtered
      out at generation time (never registered with FastMCP).
- [ ] Filtering decision is visible in `GenerationReport` (new `blocked` list) for
      logging/observability.

## Out of Scope

| Feature                                  | Reason                                                                        |
| ---------------------------------------- | ----------------------------------------------------------------------------- |
| Per-tool / per-realm read-only overrides | Not requested; single global flag is sufficient for now                       |
| Rejecting write calls at request time    | Filtering at generation time is cleaner — LLM never sees the tool as callable |

---

## User Stories

### P1: Operator restricts server to read-only Keycloak access ⭐ MVP

**User Story**: As an operator running the MCP server, I want to set
`MCP_KEYCLOAK_READ_ONLY=true` so that only GET (read) Keycloak operations are exposed as
MCP tools, and no client can trigger a write.

**Why P1**: Core requested capability; without it there's no read-only mode at all.

**Acceptance Criteria**:

1. WHEN `MCP_KEYCLOAK_READ_ONLY` is unset or `false` THEN system SHALL register all
   operations as tools (current behavior unchanged).
2. WHEN `MCP_KEYCLOAK_READ_ONLY=true` THEN system SHALL register only operations whose
   HTTP method is `GET` as MCP tools.
3. WHEN `MCP_KEYCLOAK_READ_ONLY=true` AND an operation's method is not `GET` THEN system
   SHALL NOT register it as a tool, and SHALL record its `operation_id` in
   `GenerationReport.blocked`.
4. WHEN the server starts with read-only mode active THEN an MCP client listing tools
   SHALL see only GET-derived tool names.

**Independent Test**: Set `MCP_KEYCLOAK_READ_ONLY=true`, run server, list tools via MCP
client, confirm only `get_*`-style read tools appear and no write tool is callable.

---

## Requirement Traceability

| ID   | Requirement                                                                            | Source   |
| ---- | -------------------------------------------------------------------------------------- | -------- |
| FR-1 | `Settings.read_only: bool` field, env `MCP_KEYCLOAK_READ_ONLY`, default `False`        | P1 AC1-2 |
| FR-2 | `generate_tools(..., read_only: bool = False)` skips non-GET ops when `read_only=True` | P1 AC2-3 |
| FR-3 | `GenerationReport.blocked: list[str]` records skipped operation ids                    | P1 AC3   |
| FR-4 | `build_server()` passes `settings.read_only` into `generate_tools`                     | P1 AC4   |
| FR-5 | README env var table documents `MCP_KEYCLOAK_READ_ONLY`                                | Docs     |
