# Plan: propagar summary/description do OpenAPI pros MCP tools

## Context

Servidor MCP gera tools a partir de `spec/keycloak-openapi.json`, mas descarta
`summary`/`description` de cada operation e parameter. Resultado: agente vê só
nome cru (ex: `put_admin_realms_realm`) sem saber o que a tool faz — pior
ainda em endpoints ambíguos (dezenas de `delete_admin_realms_realm_*`). Meta:
propagar essas descrições ponta a ponta pra melhorar contexto do agente.

## Root cause (confirmado via exploração)

Gap existe em 3 pontos da pipeline `spec → Operation → GeneratedTool → MCPTool`:

1. `src/keycloak_mcp/openapi/models.py:9-32` — `Operation`, `Param`,
   `RequestBodySchema` não têm campo `summary`/`description`.
2. `src/keycloak_mcp/openapi/parser.py` — `_parse_operation` (linhas 33-49) e
   `_parse_params` (linhas 62-71) nunca leem `raw_operation.get("summary")`,
   `.get("description")` nem `raw_param.get("description")`.
3. `src/keycloak_mcp/tools/generator.py:69-97` — `generate_tools()` constrói
   `GeneratedTool(...)` sem passar `description=`. Fastmcp
   (`fastmcp/tools/base.py:190-217`, `Tool.to_mcp_tool()`) usa
   `self.description` (default `None`) pra montar o `MCPTool` real exposto ao
   client.
4. `src/keycloak_mcp/openapi/validator.py:16-30` `build_input_schema()` seta
   `properties[param.name] = param.schema` sem injetar `description` — então
   nem os parâmetros individuais têm contexto no JSON schema.

## Implementação

**1. `models.py`** — adicionar campos opcionais:
```python
summary: str | None = None
description: str | None = None
```
em `Operation`. Em `Param`, adicionar `description: str | None = None`.

**2. `parser.py`** — em `_parse_operation`, capturar:
```python
summary=raw_operation.get("summary")
description=raw_operation.get("description")
```
Em `_parse_params`, capturar `description=raw_param.get("description")`.

**3. `generator.py`** — em `generate_tools()`, montar description da tool
combinando summary + description (summary como título curto, description como
corpo, caindo pra string vazia/None se ambos ausentes) e passar
`description=tool_description` no construtor de `GeneratedTool`. Regra
simples: `description = operation.description or operation.summary or None`
(ou concatenar se ambos existirem, ex: `f"{summary}\n\n{description}"`).

**4. `validator.py`** — em `build_input_schema()`, ao montar cada
`properties[param.name]`, fazer merge do `param.description` como chave
`"description"` no dict do schema (sem sobrescrever se schema já tiver uma via
`resolve_refs`).

## Arquivos a modificar

- `src/keycloak_mcp/openapi/models.py`
- `src/keycloak_mcp/openapi/parser.py`
- `src/keycloak_mcp/tools/generator.py`
- `src/keycloak_mcp/openapi/validator.py`

## Verificação

1. Rodar suite de testes existente (`pytest`) — checar se há testes de
   parser/generator que precisem de fixtures atualizadas.
2. Escrever/rodar teste rápido: parsear um operation do
   `spec/keycloak-openapi.json` que tenha `summary`/`description` (ex: alguma
   rota de `users` ou `clients`) e confirmar que `Operation.summary` e
   `Operation.description` vêm populados.
3. Rodar `generate_tools()` sobre o spec real e inspecionar 2-3
   `GeneratedTool.description` gerados — confirmar que não é `None` pra
   operations que têm summary/description no spec original.
4. Se possível, iniciar o server MCP localmente e listar tools via client
   (ex: `mcp dev` ou inspector) pra confirmar que `description` aparece no
   `tools/list` response.
