# keycloak-mcp-server

MCP server exposing the Keycloak Admin REST API as MCP tools. Tools are
generated at startup from a vendored OpenAPI spec (`spec/keycloak-openapi.json`) —
one tool per operation, name/input schema derived automatically.

## Install & run

```bash
uvx --from . keycloak-mcp-server
# or
uvx --from git+https://github.com/Ronnasayd/keyclock-mcp-server keycloak-mcp-server
```

## Configuration

Set via environment variables (or a `.env` file — **never commit it**, see `.gitignore`):

| Var                           | Required    | Notes                              |
| ----------------------------- | ----------- | ---------------------------------- |
| `MCP_KEYCLOCK_BASE_URL`       | yes         | Admin API base URL                 |
| `MCP_KEYCLOCK_AUTH_METHOD`    | yes         | `client_credentials` \| `password` |
| `MCP_KEYCLOCK_CLIENT_ID`      | conditional | both auth methods                  |
| `MCP_KEYCLOCK_CLIENT_SECRET`  | conditional | `client_credentials` only          |
| `MCP_KEYCLOCK_ADMIN_USERNAME` | conditional | `password` only                    |
| `MCP_KEYCLOCK_ADMIN_PASSWORD` | conditional | `password` only                    |
| `MCP_KEYCLOCK_DEFAULT_REALM`  | no          | fallback realm if tool omits it    |

### Auth methods

- **`client_credentials`**: service account grant, requires `MCP_KEYCLOCK_CLIENT_ID` + `MCP_KEYCLOCK_CLIENT_SECRET`.
- **`password`**: Resource Owner Password Credentials (ROPC), requires `MCP_KEYCLOCK_CLIENT_ID` +
  `MCP_KEYCLOCK_ADMIN_USERNAME` + `MCP_KEYCLOCK_ADMIN_PASSWORD`.

No automatic token refresh — if Keycloak rejects a call with 401, restart the
server process (or re-authenticate) once support for it lands.

## Adding to Claude Code

Add to your MCP config (`.mcp.json` or `claude mcp add`), choosing the env
block that matches your `MCP_KEYCLOCK_AUTH_METHOD`.

### `client_credentials`

```json
{
  "mcpServers": {
    "keycloak": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Ronnasayd/keyclock-mcp-server",
        "keycloak-mcp-server"
      ],
      "env": {
        "MCP_KEYCLOCK_BASE_URL": "http://localhost:8080",
        "MCP_KEYCLOCK_AUTH_METHOD": "client_credentials",
        "MCP_KEYCLOCK_CLIENT_ID": "your-client-id",
        "MCP_KEYCLOCK_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Or via CLI:

```bash
claude mcp add keycloak \
  --env MCP_KEYCLOCK_BASE_URL=http://localhost:8080 \
  --env MCP_KEYCLOCK_AUTH_METHOD=client_credentials \
  --env MCP_KEYCLOCK_CLIENT_ID=your-client-id \
  --env MCP_KEYCLOCK_CLIENT_SECRET=your-client-secret \
  -- uvx --from git+https://github.com/Ronnasayd/keyclock-mcp-server keycloak-mcp-server
```

### `password` (ROPC)

```json
{
  "mcpServers": {
    "keycloak": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Ronnasayd/keyclock-mcp-server",
        "keycloak-mcp-server"
      ],
      "env": {
        "MCP_KEYCLOCK_BASE_URL": "http://localhost:8080",
        "MCP_KEYCLOCK_AUTH_METHOD": "password",
        "MCP_KEYCLOCK_CLIENT_ID": "your-client-id",
        "MCP_KEYCLOCK_ADMIN_USERNAME": "your-admin-username",
        "MCP_KEYCLOCK_ADMIN_PASSWORD": "your-admin-password"
      }
    }
  }
}
```

Or via CLI:

```bash
claude mcp add keycloak \
  --env MCP_KEYCLOCK_BASE_URL=http://localhost:8080 \
  --env MCP_KEYCLOCK_AUTH_METHOD=password \
  --env MCP_KEYCLOCK_CLIENT_ID=your-client-id \
  --env MCP_KEYCLOCK_ADMIN_USERNAME=your-admin-username \
  --env MCP_KEYCLOCK_ADMIN_PASSWORD=your-admin-password \
  -- uvx --from git+https://github.com/Ronnasayd/keyclock-mcp-server keycloak-mcp-server
```

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
