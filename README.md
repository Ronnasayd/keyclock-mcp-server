# keycloak-mcp-server

MCP server exposing the Keycloak Admin REST API as MCP tools. Tools are
generated at startup from a vendored OpenAPI spec (`spec/keycloak-openapi.json`) —
one tool per operation, name/input schema derived automatically.

## Install & run

```bash
uvx --from . keycloak-mcp-server
```

## Configuration

Set via environment variables (or a `.env` file — **never commit it**, see `.gitignore`):

| Var                 | Required    | Notes                              |
| ------------------- | ----------- | ----------------------------------- |
| `KEYCLOAK_BASE_URL` | yes         | Admin API base URL                 |
| `AUTH_METHOD`       | yes         | `client_credentials` \| `password` |
| `CLIENT_ID`         | conditional | both auth methods                  |
| `CLIENT_SECRET`     | conditional | `client_credentials` only          |
| `ADMIN_USERNAME`    | conditional | `password` only                    |
| `ADMIN_PASSWORD`    | conditional | `password` only                    |
| `DEFAULT_REALM`     | no          | fallback realm if tool omits it    |

### Auth methods

- **`client_credentials`**: service account grant, requires `CLIENT_ID` + `CLIENT_SECRET`.
- **`password`**: Resource Owner Password Credentials (ROPC), requires `CLIENT_ID` +
  `ADMIN_USERNAME` + `ADMIN_PASSWORD`.

No automatic token refresh — if Keycloak rejects a call with 401, restart the
server process (or re-authenticate) once support for it lands.

## Syncing the vendored spec

The spec is fetched once and committed. To refresh it from the official source:

```bash
python scripts/sync_openapi.py --dry-run   # preview the diff
python scripts/sync_openapi.py             # overwrite spec/keycloak-openapi.json
```

## Development

```bash
uv venv
uv pip install -e ".[dev]"
pytest
```
