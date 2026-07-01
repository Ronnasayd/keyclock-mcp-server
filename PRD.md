# PRD — Keycloak MCP Server (OpenAPI-Driven)

## 1. Executive Summary

Servidor MCP (Model Context Protocol) em Python/FastMCP que expõe a **Keycloak Admin REST API** como um conjunto de tools consumíveis por LLMs/agentes. As tools são **geradas via metaprogramação** a partir do arquivo `openapi.json` oficial do Keycloak (vendorizado localmente no repo), garantindo 100% de cobertura da spec sem manutenção manual tool-a-tool. Cada `operationId` do OpenAPI vira exatamente uma tool MCP. Requests são validados contra o schema de input antes de disparar a chamada HTTP; respostas de erro do Keycloak são repassadas ao cliente MCP de forma estruturada (status + corpo).

Uso alvo: times de dev/plataforma que precisam automatizar administração de Keycloak (realms, clients, users, roles, etc.) via agentes de IA, sem escrever wrapper manual para cada endpoint.

## 2. Vision & Goals

- **Visão:** qualquer endpoint da Admin REST API do Keycloak deve estar disponível como tool MCP, sem esforço manual de manutenção — a spec é a fonte da verdade.
- **Metas MVP (2-4 semanas):**
  - Geração automática de 100% das tools a partir do `openapi.json` vendorizado.
  - Autenticação configurável (client credentials OU ROPC/admin password).
  - Suporte multi-realm por parâmetro de chamada.
  - Validação de input via schema antes de request.
  - Erros do Keycloak repassados de forma estruturada.

## 3. Target Users

- **Persona única:** devs/times de plataforma (múltiplos devs na empresa) que operam Keycloak via agentes de IA (Claude Code e similares). Não é produto end-user; é ferramenta interna/dev-tool, mas com padrão de qualidade "compartilhável entre time" (README, config clara, testes).

## 4. MVP Features

1. Parser de `openapi.json` (vendorizado, versionado no repo) → modelo interno de operations (path, method, operationId, params, request/response schemas).
2. Gerador de tools MCP via metaprogramação: 1 tool por `operationId`, nome/schema derivados automaticamente.
3. Cliente HTTP genérico para Admin REST API (base URL configurável via env).
4. Módulo de autenticação configurável:
   - Client credentials (service account) via env.
   - ROPC (username/password admin) via env.
   - Seleção do método via config, sem hardcode.
5. Parâmetro `realm` obrigatório/opcional por tool conforme endpoint (suporte multi-realm nativo).
6. Validação de input (params + body) contra schema OpenAPI antes de disparar request.
7. Tratamento de erro: captura resposta de erro do Keycloak (status code + body) e repassa formatado ao chamador MCP.
8. Logging básico (INFO/ERROR) de request/response — status, método, path — sem logar PII (senhas, tokens, payloads sensíveis).
9. Comando/script de re-sync do `openapi.json` vendorizado (atualização manual quando Keycloak lança nova versão).
10. Testes automatizados: geração de tools (contra spec fixture), autenticação (mock), tratamento de erro.

## 5. Architecture

```
┌─────────────────────────────┐
│   Claude / Agente MCP client │
└──────────────┬───────────────┘
               │ MCP protocol (stdio/SSE)
┌──────────────▼───────────────┐
│      Keycloak MCP Server      │
│         (Python/FastMCP)      │
│                                │
│  ┌──────────────────────────┐  │
│  │ OpenAPI Parser            │  │
│  │ (openapi.json vendorizado)│  │
│  └──────────┬───────────────┘  │
│             │ gera              │
│  ┌──────────▼───────────────┐  │
│  │ Tool Generator (metaprog) │  │
│  │  1 tool / operationId     │  │
│  └──────────┬───────────────┘  │
│             │                   │
│  ┌──────────▼───────────────┐  │
│  │ Auth Manager               │
│  │ (client_credentials|ROPC)  │
│  └──────────┬───────────────┘  │
│             │                   │
│  ┌──────────▼───────────────┐  │
│  │ HTTP Client + Validator     │
│  │ (input schema validation)   │
│  └──────────┬───────────────┘  │
└─────────────┼───────────────────┘
              │ HTTPS
┌─────────────▼───────────────┐
│  Keycloak Admin REST API     │
│  (multi-realm via param)     │
└───────────────────────────────┘
```

## 6. Tech Stack

- **Runtime:** Python 3.11+
- **MCP framework:** FastMCP
- **Parsing OpenAPI:** `openapi-core` ou `openapi-spec-validator` + parsing custom para extrair operations/schemas
- **HTTP client:** `httpx` (async)
- **Validação:** `jsonschema` ou `pydantic` gerado a partir dos schemas OpenAPI (avaliar codegen: `datamodel-code-generator`)
- **Config:** env vars (`.env` + `pydantic-settings`)
- **Testes:** `pytest` + `pytest-asyncio` + `respx`/`httpx` mock
- **Spec vendorizada:** `openapi.json` commitado em `spec/keycloak-openapi.json`, com script `scripts/sync_openapi.py` para re-fetch manual da URL oficial

## 7. Data Model

- Sem persistência própria — stateless, proxy de chamadas.
- Config (env): `KEYCLOAK_BASE_URL`, `AUTH_METHOD` (`client_credentials`|`password`), `CLIENT_ID`, `CLIENT_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DEFAULT_REALM` (opcional).
- Cache em memória: token de acesso (com refresh automático antes de expirar), modelo de operations parseado do OpenAPI (carregado 1x no startup).

## 8. User Flows

**Flow 1 — Startup:**

1. Server lê env config → decide método de auth.
2. Parser carrega `spec/keycloak-openapi.json` → gera N tools.
3. Server registra tools no FastMCP e sobe (stdio/SSE).

**Flow 2 — Chamada de tool:**

1. Agente invoca tool (ex: `create_user`) com params incluindo `realm`.
2. Server valida input contra schema OpenAPI da operation.
3. Auth Manager garante token válido (renova se expirado).
4. HTTP Client monta request (path/method/body) e chama Keycloak.
5. Sucesso → retorna resposta ao agente. Erro → repassa status+body formatado.

**Flow 3 — Atualização de spec:**

1. Dev roda `scripts/sync_openapi.py` → baixa nova versão da URL oficial.
2. Diff revisado, commitado no repo.
3. Próximo boot do server já gera tools atualizadas automaticamente.

## 9. KPIs

- % de operations do OpenAPI cobertas por tool gerada (meta: 100%).
- Taxa de erro de validação de input pré-request (deve capturar erros antes do round-trip HTTP).
- Tempo de startup do server (geração de tools não deve ser gargalo, meta <2s para spec completa).
- Cobertura de testes automatizados (meta: >80% no gerador e auth manager).

## 10. Timeline (Normal — 2-4 semanas)

- **Semana 1:** parser do OpenAPI + modelo de operations + POC de geração de 1 tool manual validando abordagem.
- **Semana 2:** gerador de tools completo (metaprogramação) + Auth Manager (ambos métodos) + HTTP client.
- **Semana 3:** validação de input, tratamento de erro estruturado, multi-realm, logging.
- **Semana 4:** testes, script de sync da spec, README, hardening, revisão de segurança (secrets/PII em logs).

## 11. Risks

- **Spec desatualizada:** vendorização manual pode ficar defasada vs. versão real do Keycloak em produção → mitigar com script de sync + doc de processo de atualização.
- **Schemas OpenAPI incompletos/inconsistentes:** Keycloak's spec pode ter gaps (params mal tipados) → geração automática pode falhar silenciosamente em alguns endpoints; precisa fallback/log de operations que falharam ao gerar tool.
- **Auth token leak em logs:** risco de PII/secrets vazarem em logs de debug → política clara de "nunca logar body/token", enforced em code review.
- **Volume de tools (100+):** pode sobrecarregar contexto do agente MCP client → considerar filtragem/tagging futuro (fora do MVP, mas registrar como débito).

## 12. Constraints

- Uso do skill `mcp-builder` como guia de construção do server (padrões de tool design, já disponível no ambiente).
- Dados de identidade (users, senhas, PII) trafegam pelo server → nunca logar payloads sensíveis; secrets só via env, nunca hardcoded.
- Greenfield — sem código legado a integrar.

## Implicit Requirements

#### IR-1 Renovação de token

- **Decision:** token OAuth não é renovado automaticamente pelo server.
- **Behavior:** Auth Manager não faz refresh proativo nem reativo (401) — se o token expirar, a chamada falha e o usuário/agente deve fornecer um novo token (reautenticar).
- **Rationale:** simplicidade no MVP; server fica stateless quanto a ciclo de vida de token.
- **Deferred:** refresh automático (proativo ou reativo) fica para v1.1 se necessário.

#### IR-2 Retry em falha de rede

- **Decision:** sem retry automático em nenhuma chamada (GET, POST, PUT, DELETE).
- **Behavior:** falha de rede/timeout contra Keycloak sobe direto como erro ao agente MCP, sem tentativa automática.
- **Rationale:** evita duplicação silenciosa de efeitos colaterais (ex: criar user 2x) e mantém comportamento previsível.
- **Deferred:** nenhum — decisão final, não revisitar sem novo requisito explícito.

#### IR-3 Operation sem operationId na spec

- **Decision:** gerar operationId sintético (`{method}_{path_slug}`) quando a operation não declarar `operationId`.
- **Behavior:** geração não falha nem pula a operation; loga warning informando nome sintético usado.
- **Rationale:** maximiza cobertura (meta 100% das operations) mesmo com specs incompletas.
- **Deferred:** —

#### IR-4 Gestão de secrets

- **Decision:** secrets (CLIENT_SECRET, ADMIN_PASSWORD) só via env var, sem integração com secret manager externo.
- **Behavior:** README deve alertar explicitamente para não commitar `.env`; sem abstração de secret provider no MVP.
- **Rationale:** escopo de dev-tool interno, MVP não precisa da complexidade de Vault/AWS SM.
- **Deferred:** suporte a secret manager externo — avaliar se demanda do time surgir.

#### IR-5 Erros HTTP do Keycloak (incl. 403)

- **Decision:** todo erro (incluindo 403 Forbidden) é repassado cru — status code + body original do Keycloak, sem tratamento especial ou hints adicionados.
- **Behavior:** consistente com a decisão geral de erro (seção 4, item 7); nenhuma lógica condicional por status code.
- **Rationale:** manter comportamento uniforme e previsível; evita manutenção de mensagens customizadas por status.
- **Deferred:** —

#### IR-6 Distribuição do server

- **Decision:** distribuição via `uvx` (execução direta do pacote Python sem instalação prévia).
- **Behavior:** dev roda `uvx keycloak-mcp-server` (ou nome do pacote); config via env vars/`.env` local. Sem Docker/container no MVP.
- **Rationale:** mais simples pro fluxo de dev individual usando MCP client (Claude Code etc), sem exigir infra de container.
- **Deferred:** empacotamento Docker/serviço compartilhado via SSE — fase 2, se necessidade de servidor centralizado surgir.

## 13. Out of Scope (MVP)

- Painel web de administração/monitoramento (fase 2, se necessário).
- Validação de response/output contra schema (só input no MVP).
- Agrupamento de tools por recurso (mantém 1:1 com operationId).
- Fetch automático de openapi.json em runtime (spec é vendorizada; sync é manual via script).
- Multi-tenancy de credenciais (1 conjunto de credenciais por instância do server; multi-realm é suportado, multi-tenant de auth não).
- Refresh automático de token (proativo ou reativo) — ver IR-1.
- Retry automático em falha de rede — ver IR-2.
- Integração com secret manager externo (Vault, AWS SM, etc.) — ver IR-4.
- Empacotamento Docker / servidor SSE compartilhado — ver IR-6.
