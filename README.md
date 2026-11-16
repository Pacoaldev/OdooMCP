<div align="center">

<img src="https://github.com/user-attachments/assets/23669ce4-0dc6-4ef1-b03d-6ffa7fb7ed63" alt="odoomcp logo" width="150">

# odoomcp

**A direct, permission-aware bridge between AI assistants and Odoo.**

Explore, query and update business data, handle attachments and trigger supported workflows through the Model Context Protocol — using the AI client you already work with.

[![CI](https://github.com/Pacoaldev/OdooMCP/actions/workflows/ci.yml/badge.svg)](https://github.com/Pacoaldev/OdooMCP/actions/workflows/ci.yml)  [![codecov](https://codecov.io/gh/Pacoaldev/OdooMCP/branch/main/graph/badge.svg)](https://codecov.io/gh/Pacoaldev/OdooMCP)  [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)  [![Checked with ty](https://img.shields.io/badge/checked%20with-ty-blue?labelColor=orange)](https://github.com/astral-sh/ty)  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**English** · [Español](README.es.md)

</div>

---

## Documentation map

Use this guide as a route through the project: start with a working connection, configure the access model that fits your environment, then explore the available operations.

**01 · Understand the project**

- [What it does](#what-it-does)
- [Quick start](#quick-start)
- [Connect your client](#connect-your-client)
- [Alternative installs](#alternative-installs)

**02 · Configure the connection**

- [Configuration](#configuration)
- [Transports](#transports)
- [Setting up Odoo (standard mode)](#setting-up-odoo-standard-mode)
- [YOLO mode](#yolo-mode)

**03 · Work with Odoo data**

- [Tools reference](#tools-reference)
- [Field selection and per-call context](#field-selection-and-per-call-context)
- [Resource URIs](#resource-uris)
- [How it works](#how-it-works)

**04 · Operate safely**

- [Security](#security)
- [Troubleshooting](#troubleshooting)

**05 · Develop and contribute**

- [Development and testing](#development-and-testing)
- [License](#license)
- [Contributing](#contributing)
- [Support](#support)

---

## Start with what you need

- **Get connected:** [Quick start](#quick-start)
- **Choose an installation:** [Alternative installs](#alternative-installs)
- **Configure access:** [Configuration](#configuration)
- **Explore the toolset:** [Tools reference](#tools-reference)
- **Review security:** [Security](#security)

## 01 · Understand the project

### What it does

An MCP server that translates natural-language requests from an AI assistant into
authenticated Odoo operations: reads, writes, aggregations, file handling and workflow
methods. It handles authentication, access control, field selection, data formatting and
error handling, and presents Odoo data in an LLM-friendly hierarchical text format.

Things you can ask your assistant once it is connected:

- "Show me all customers from Spain"
- "Find products with stock below 10 units"
- "List today's sales orders over $1000"
- "Create a new customer contact for Acme Corporation"
- "Update the phone number for customer John Doe to +1-555-0123"
- "Change the status of order SO/2024/001 to confirmed"
- "Delete the test contact we created earlier"

### Feature map

| Area | What you get |
|------|--------------|
| CRUD | Search, read, count, create, update and delete across enabled models |
| Bulk operations | Batch create/update of up to 100 records in one atomic transaction |
| Analytics | Server-side grouping and sums (`formatted_read_group` on Odoo 19+, `read_group` fallback) |
| Files | Read and upload attachments and binary fields; post to the record chatter |
| Session context | Connected user, timezone and company scope injected into session instructions |
| Intelligence | Smart field selection, credential-like fields withheld, LLM-optimized output |
| Access control | API key or user/password auth, model allowlist, per-call company/language context |
| Localization | Responses in your preferred Odoo language (`ODOO_LOCALE`, per-call `lang`) |
| Compatibility | Works with any Odoo instance in YOLO mode; with the MCP module for production |

### Quick start

1. Install [UV](https://docs.astral.sh/uv/) on the machine that runs your AI client:

   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Point your client at the server with your Odoo credentials:

   ```json
   {
     "mcpServers": {
       "odoo": {
         "command": "uvx",
         "args": ["odoomcp"],
         "env": {
           "ODOO_URL": "https://your-odoo-instance.com",
           "ODOO_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```

3. Restart your terminal so UV is on the `PATH`, then start asking.

Two ways to talk to Odoo:

- **Standard mode (production)**: Odoo 16.0+ with the
  [Odoo MCP module](https://apps.odoo.com/apps/modules/19.0/mcp_server) installed.
  Model-level permissions, audited access.
- **YOLO mode (dev/testing/demos)**: connects to any standard Odoo with XML-RPC enabled.
  No module required. Bypasses MCP access controls — see [YOLO mode](#yolo-mode).

### Connect your client

The server runs on the machine where the AI client is installed, not on the Odoo server.
Every client below takes the same command, arguments and environment — only the config
file location differs.

<details>
<summary>Claude Desktop</summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoomcp"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_API_KEY": "your-api-key-here",
        "ODOO_DB": "your-database-name"
      }
    }
  }
}
```
</details>

<details>
<summary>Claude Code</summary>

Add to `.mcp.json` in your project root, or run:

```bash
claude mcp add odoo \
  --env ODOO_URL=https://your-odoo-instance.com \
  --env ODOO_API_KEY=your-api-key-here \
  --env ODOO_DB=your-database-name \
  -- uvx odoomcp
```
</details>

<details>
<summary>Cursor</summary>

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoomcp"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_API_KEY": "your-api-key-here",
        "ODOO_DB": "your-database-name"
      }
    }
  }
}
```
</details>

<details>
<summary>VS Code (with GitHub Copilot)</summary>

Add to `.vscode/mcp.json` in your workspace. Note that VS Code uses `"servers"` as the
root key, not `"mcpServers"`:

```json
{
  "servers": {
    "odoo": {
      "type": "stdio",
      "command": "uvx",
      "args": ["odoomcp"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_API_KEY": "your-api-key-here",
        "ODOO_DB": "your-database-name"
      }
    }
  }
}
```
</details>

<details>
<summary>Windsurf</summary>

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvx",
      "args": ["odoomcp"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_API_KEY": "your-api-key-here",
        "ODOO_DB": "your-database-name"
      }
    }
  }
}
```
</details>

<details>
<summary>Zed</summary>

Add to `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "odoo": {
      "command": {
        "path": "uvx",
        "args": ["odoomcp"],
        "env": {
          "ODOO_URL": "https://your-odoo-instance.com",
          "ODOO_API_KEY": "your-api-key-here",
          "ODOO_DB": "your-database-name"
        }
      }
    }
  }
}
```
</details>

### Alternative installs

<details>
<summary>Docker</summary>

Run with Docker — no Python installation required:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "ODOO_URL=http://host.docker.internal:8069",
        "-e", "ODOO_API_KEY=your-api-key-here",
        "Pacoaldev/OdooMCP"
      ]
    }
  }
}
```

> **Note:** Use `host.docker.internal` instead of `localhost` to connect to Odoo running on the host machine.

For HTTP transport:

```bash
docker run --rm -p 8000:8000 \
  -e ODOO_URL=http://host.docker.internal:8069 \
  -e ODOO_API_KEY=your-api-key-here \
  Pacoaldev/OdooMCP --transport streamable-http --host 0.0.0.0
```

> ⚠️ **Security**: the HTTP transport has no built-in authentication — anyone who can reach the port gets Odoo access through the server's credentials. Publish the port only on trusted networks, or front it with an authenticating reverse proxy. See [Transports](#transports).

The image is also available on GHCR: `ghcr.io/pacoaldev/odoomcp`
</details>

<details>
<summary>pip / pipx</summary>

```bash
# Install globally
pip install odoomcp

# Or use pipx for an isolated environment
pipx install odoomcp
```

Then use `odoomcp` as the command in your MCP configuration.
</details>

<details>
<summary>From source</summary>

```bash
git clone https://github.com/Pacoaldev/OdooMCP.git
cd odoomcp
pip install -e .
```

Then use the full path to the package in your MCP configuration.
</details>

## 02 · Configure the connection

### Configuration

#### Required environment variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ODOO_URL` | Yes | Your Odoo instance URL | `https://mycompany.odoo.com` |
| `ODOO_API_KEY` | Yes* | API key for authentication | `0ef5b399e9ee9c11b053dfb6eeba8de473c29fcd` |
| `ODOO_USER` | Yes* | Username (if not using API key) | `admin` |
| `ODOO_PASSWORD` | Yes* | Password (if not using API key) | `admin` |
| `ODOO_DB` | No | Database name (auto-detected if not set) | `mycompany` |
| `ODOO_LOCALE` | No | Language/locale for Odoo responses | `es_ES`, `fr_FR`, `de_DE` |
| `ODOO_ALLOWED_COMPANIES` | No | Comma-separated company IDs to scope all operations to (multi-company setups) | `1`, `1,3` |
| `ODOO_YOLO` | No | YOLO mode - bypasses MCP security (⚠️ DEV ONLY) | `off`, `read`, `true` |
| `ODOO_MCP_ENABLE_METHOD_CALLS` | No | Enable the `call_model_method` tool — requires `ODOO_YOLO=true` (⚠️ Dangerous, see [`call_model_method`](#call_model_method)) | `false`, `true` |
| `ODOO_RPC_TRANSPORT` | No | RPC protocol in YOLO mode: `auto` (JSON-2 on Odoo 19 and later with an API key, else XML-RPC), `xmlrpc`, or `json2` for Odoo's JSON-2 API (Odoo 19 and later, API key only) | `auto`, `json2` |

*Either `ODOO_API_KEY` or both `ODOO_USER` and `ODOO_PASSWORD` are required. In YOLO mode
over XML-RPC, `ODOO_USER` is required even when using an API key. Over JSON-2 the API key
alone is enough, because Odoo reads the user from the key.

**Notes:**
- If database listing is restricted on your server, you must specify `ODOO_DB`
- API key authentication is recommended for better security
- The server also loads environment variables from a `.env` file in the working directory
- In standard mode, the server keeps each model's MCP permissions for 5 minutes. If you
  remove a permission in Odoo, the next call is refused at once, because the MCP module
  checks every call. If you grant a permission, it can take up to 5 minutes to work.
  Restart the server to apply it at once.

#### Advanced variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ODOO_MCP_DEFAULT_LIMIT` | `25` | Default number of records returned per search |
| `ODOO_MCP_MAX_LIMIT` | `100` | Maximum allowed record limit per request |
| `ODOO_MCP_MAX_SMART_FIELDS` | `15` | Maximum fields returned by smart field selection |
| `ODOO_MCP_LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `ODOO_MCP_LOG_JSON` | `false` | Enable structured JSON log output |
| `ODOO_MCP_LOG_FILE` | — | Path for rotating log file (10 MB, 5 backups) |
| `ODOO_MCP_LOG_FORMAT` | — | Custom Python logging format string (default: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`) |
| `ODOO_MCP_SLOW_OPERATION_THRESHOLD_MS` | `1000` | Threshold in milliseconds above which an operation is logged as slow |
| `ODOO_MCP_TRANSPORT` | `stdio` | Transport type (`stdio`, `streamable-http`) |
| `ODOO_MCP_HOST` | `localhost` | Host to bind for HTTP transport |
| `ODOO_MCP_PORT` | `8000` | Port to bind for HTTP transport |
| `ODOO_MCP_ALLOWED_HOSTS` | — | Comma-separated `Host` headers to accept for HTTP transport (DNS-rebinding protection). Set when running `streamable-http` behind a reverse proxy that forwards an external host, e.g. `odoo.example.com,localhost`. IPv6 literals may be bracketed or bare (`[::1]:8000`, `::1`). **Unset, protection is only auto-enabled for a loopback bind** — binding any other host (e.g. `0.0.0.0`) runs with no `Host`/`Origin` validation at all. |
| `ODOO_MCP_SESSION_IDLE_TIMEOUT` | — | Seconds of inactivity before a `streamable-http` session is closed and its server-side state freed, e.g. `600`. Unset means sessions never expire. |
| `ODOO_MCP_MAX_BINARY_SIZE` | `52428800` | Maximum bytes returned by a single binary/attachment `resources/read`. Checked before the payload is fetched (for record fields, a `bin_size` probe on Odoo 19 and older, and the size of the backing attachment or a `field.size` count on Odoo 20; for attachments, the stored `file_size`), so an oversized read is refused with a clean error instead of being pulled into memory and re-encoded to base64 for the wire. On Odoo 20 a non-stored binary field (such as `avatar_128`), or a stored one whose attachment the user cannot read, is checked only after the fetch. |

#### Multi-company scoping (`ODOO_ALLOWED_COMPANIES`)

In multi-company databases, the authenticated user's default company applies to every
record the server creates, and record visibility spans all of the user's allowed
companies. Setting `ODOO_ALLOWED_COMPANIES` injects `allowed_company_ids` into the
context of every RPC call, so record rules, `env.company` and create defaults are limited
to the listed companies. A useful pattern is configuring one MCP server entry per
company, sharing a single Odoo user:

```json
{
  "mcpServers": {
    "odoo-company-a": {
      "command": "uvx",
      "args": ["odoomcp"],
      "env": { "ODOO_URL": "...", "ODOO_API_KEY": "...", "ODOO_ALLOWED_COMPANIES": "1" }
    },
    "odoo-company-b": {
      "command": "uvx",
      "args": ["odoomcp"],
      "env": { "ODOO_URL": "...", "ODOO_API_KEY": "...", "ODOO_ALLOWED_COMPANIES": "3" }
    }
  }
}
```

At startup, the server makes sure that each ID is one of the user's companies, and it
does not start otherwise. If the user cannot read their own `res.users` record (standard
mode without `res.users` enabled), the check is skipped with a warning, and Odoo refuses
a foreign company on each call instead. The first ID is the active company: Odoo uses it
for create defaults, and `get_current_context` and the session instructions show it. A
call can narrow the scope to some of the listed companies, but never widen it.

Note this is context-level scoping, not a security boundary: the credentials can still
access every company the Odoo user is allowed to. For hard isolation, restrict the user's
allowed companies in Odoo itself.

### Transports

#### stdio (default)

Standard input/output — what desktop AI applications like Claude Desktop use. No extra
configuration:

```bash
uvx odoomcp
```

#### streamable-http

HTTP transport for remote connectivity and REST-style access.

> ⚠️ **Security**: this transport has **no built-in client authentication**. Any client
> that can reach the port can use every tool and resource with the Odoo credentials the
> server holds — including writes in YOLO full-access mode. Keep the default `localhost`
> bind unless the network is trusted, and front the server with an authenticating reverse
> proxy (e.g. nginx with basic auth or OAuth) for remote access. The server logs a
> warning when binding a non-loopback host.

```bash
# Run with HTTP transport (localhost only — safe default)
uvx odoomcp --transport streamable-http --port 8000

# Binding 0.0.0.0 exposes the server to the network — see the security note above
uvx odoomcp --transport streamable-http --host 0.0.0.0 --port 8000

# Or use environment variables
export ODOO_MCP_TRANSPORT=streamable-http
export ODOO_MCP_HOST=0.0.0.0
export ODOO_MCP_PORT=8000
uvx odoomcp
```

The HTTP endpoint will be available at: `http://localhost:8000/mcp/`

> **Note**: SSE (Server-Sent Events) transport has been deprecated in MCP protocol
> version 2025-03-26. Use streamable-http instead.

> **Note**: The HTTP transport refuses request bodies over 4 MiB with HTTP 413. It holds
> at most 10,000 open sessions and answers new ones with HTTP 503 beyond that. If
> `ODOO_MCP_SESSION_IDLE_TIMEOUT` is unset, sessions never expire, so set it for a
> long-running public server.

<details>
<summary>Running streamable-http transport for remote access</summary>

```json
{
  "mcpServers": {
    "odoo-remote": {
      "command": "uvx",
      "args": ["odoomcp", "--transport", "streamable-http", "--port", "8080"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_API_KEY": "your-api-key-here",
        "ODOO_DB": "your-database-name"
      }
    }
  }
}
```
</details>

### Setting up Odoo (standard mode)

1. **Install the MCP module**:
   - Download the [mcp_server](https://apps.odoo.com/apps/modules/19.0/mcp_server) module
   - Install it in your Odoo instance
   - Navigate to Settings > MCP Server

2. **Enable models for MCP access**:
   - Go to Settings > MCP Server > Enabled Models
   - Add models you want to access (e.g., res.partner, product.product)
   - Configure permissions (read, write, create, delete) per model

3. **Generate an API key**:
   - Go to Settings > Users & Companies > Users
   - Select your user
   - Under the "API Keys" tab, create a new key
   - On Odoo 20, give the key the RPC scope (`rpc`). Odoo 20 accepts a key on its RPC
     routes only with that scope.
   - Copy the key for your MCP configuration

4. **Grant MCP access to the user**:
   - Add the user to the MCP User group in the access rights of the user
   - Recent module versions refuse API keys and password logins of users outside this
     group. The server then reports the reason from the module at startup.

### YOLO mode

YOLO mode lets the server connect directly to any standard Odoo instance **without the
MCP module**. It bypasses all MCP access controls and is intended **ONLY for development,
testing and demos**.

**Never use YOLO mode in production.**

#### Levels

| Level | Flag | Allows | Blocks | Use for |
|-------|------|--------|--------|---------|
| Read-only | `ODOO_YOLO=read` | All reads (search, read, count) | All writes; shows READ-ONLY indicators | Demos, testing |
| Full access | `ODOO_YOLO=true` | Everything — full CRUD on every model | Nothing; shows FULL ACCESS warnings | Isolated environments only |

#### Configuration examples

<details>
<summary>Read-only YOLO mode (safer for demos)</summary>

```json
{
  "mcpServers": {
    "odoo-demo": {
      "command": "uvx",
      "args": ["odoomcp"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_USER": "admin",
        "ODOO_PASSWORD": "admin",
        "ODOO_DB": "demo",
        "ODOO_YOLO": "read"
      }
    }
  }
}
```
</details>

<details>
<summary>Full access YOLO mode (⚠️ use with extreme caution)</summary>

```json
{
  "mcpServers": {
    "odoo-test": {
      "command": "uvx",
      "args": ["odoomcp"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_USER": "admin",
        "ODOO_PASSWORD": "admin",
        "ODOO_DB": "test",
        "ODOO_YOLO": "true"
      }
    }
  }
}
```
</details>

#### When to use it

Good fit: local development with test data, quick demos with non-sensitive data, testing
MCP clients before installing the module, prototyping in isolated environments.

Never: production environments, instances with real customer data, shared development
servers, anything with sensitive information.

#### Security notes

- Connects directly to Odoo's standard XML-RPC endpoints, or to JSON-2 (`/json/2`) on
  Odoo 19 and later with an API key (see `ODOO_RPC_TRANSPORT`)
- Bypasses all MCP access controls and model restrictions
- No rate limiting is applied
- All operations are logged but not restricted
- Model listing shows 200+ models instead of just enabled ones
- In full YOLO mode (`true`), the create, update and delete tools reach every model,
  scheduled actions (`ir.cron`) and server actions (`ir.actions.server`) included.
  `call_model_method` refuses to run them directly, but a changed action runs on its next
  schedule or trigger. This is the same power that an administrator has in the Odoo UI.

## 03 · Work with Odoo data

### Tools reference

| Tool | Purpose |
|------|---------|
| `search_records` | Search records in any model with filters, field selection and pagination |
| `get_record` | Fetch one record by ID |
| `get_fields` | Describe a model's schema: types, labels, relations, selection options |
| `list_models` | List models enabled for MCP access |
| `list_resource_templates` | List the resource URI patterns the server exposes |
| `get_current_context` | Show the session user, timezone, company scope and datetime guidance |
| `aggregate_records` | Server-side grouping and aggregation (counts, sums, group-bys) |
| `create_record` / `create_records` | Create one record, or up to 100 in one atomic transaction |
| `update_record` / `update_records` | Update one record, or up to 100 (same or per-record values) |
| `delete_record` | Delete a record |
| `read_attachment` | Read a file: text, extracted PDF/Office text, inline image or download link |
| `list_record_attachments` | List files attached to a record, newest first |
| `upload_attachment` | Attach a file to a record (base64, up to about 2.9 MB) |
| `post_message` | Post a message to a record's chatter (`mail.thread`) |
| `call_model_method` | Opt-in escape hatch for workflow methods (full YOLO only) |

#### Reading data

##### `search_records`

```json
{
  "model": "res.partner",
  "domain": [["is_company", "=", true], ["country_id.code", "=", "ES"]],
  "fields": ["name", "email", "phone"],
  "limit": 10
}
```

**Field selection:**
- Omit `fields` or set to `null`: smart selection of common fields
- Specify a field list: only those fields
- Empty list `[]` is treated like `null` (smart defaults)
- `["__all__"]`: all fields (with caution) — credential-like fields are withheld and
  listed in the response's `note`; request them explicitly by name if needed

##### `get_record`

```json
{
  "model": "res.partner",
  "record_id": 42,
  "fields": ["name", "email", "street", "city"]
}
```

Same field selection rules as `search_records`. Responses also include
`related_summaries`: display names for one2many/many2many collections holding at most 5
ids, so small relations are readable without extra lookups.

##### `get_fields`

Describe a model's fields — type, label, required/readonly, relation target, and
selection options. Use it to discover a model's schema before reading or writing records.
Omit `attributes` for the curated default set (`type`, `string`, `required`, `readonly`,
`relation`, `selection`); an explicit list replaces the curated set — include the
defaults in your list if you still need them (e.g. `["type", "string", "help", "store"]`).
Omit `field_names` for a short view: the 60 most relevant value fields, plus every
one2many, many2many, file and HTML field, with selection lists cut at 20 values. The
response then includes `omitted`, the number of fields left out, and a `note`. Pass
`["__all__"]` for every field, or name the fields you need. These two forms do not cut
selection lists. An empty list `[]` for either parameter is treated like omitting it.

```json
{
  "model": "res.partner",
  "field_names": ["name", "email", "parent_id"]
}
```

##### `get_current_context`

Return the current session context: the connected user, their timezone, the active
company plus any other allowed companies, and UTC datetime-handling guidance. Useful
when unsure which user or company a request runs as, or how to interpret datetimes.
Spec-compliant clients also receive this context through the `initialize` response
instructions.

```json
{}
```

##### `list_models`

List all models enabled for MCP access.

```json
{}
```

##### `list_resource_templates`

List available resource URI templates and their patterns.

```json
{}
```

##### `aggregate_records`

Server-side aggregation. Use this whenever the question is "totals/counts/groupings"
rather than "list of records" — it pushes the work down to PostgreSQL instead of pulling
raw rows. Dispatches to `formatted_read_group` on Odoo 19+ (the new dedicated method) and
falls back to `read_group` with response normalization on older versions. Callers see a
consistent response shape on every supported version. When `aggregates` is omitted,
defaults to `["__count"]` so each group always carries a count. When more groups exist
beyond the requested page, the response sets `has_more: true` and a `next_hint` with the
follow-up offset.

```json
{
  "model": "sale.order",
  "groupby": ["date_order:month"],
  "aggregates": ["amount_total:sum"],
  "domain": [["state", "in", ["sale", "done"]]]
}
```

```json
{
  "model": "res.partner",
  "groupby": ["country_id"]
}
```

#### Writing data

##### `create_record`

```json
{
  "model": "res.partner",
  "values": {
    "name": "New Customer",
    "email": "customer@example.com",
    "is_company": true
  }
}
```

##### `create_records`

Create several records of one model in one call. The call accepts at most 100 records.
It is one transaction: either every record is created or none.

```json
{
  "model": "res.partner",
  "records": [
    {"name": "Customer A", "email": "a@example.com"},
    {"name": "Customer B", "email": "b@example.com"}
  ]
}
```

##### `update_record`

```json
{
  "model": "res.partner",
  "record_id": 42,
  "values": {
    "phone": "+1234567890",
    "website": "https://example.com"
  }
}
```

##### `update_records`

Update several records of one model in one call, with at most 100 distinct records. If
any ID does not exist, nothing is written. Archived records can be updated, for example
to unarchive them with `"active": true`. Use one of two forms.

The same values on every record, on any Odoo version:

```json
{
  "model": "res.partner",
  "record_ids": [42, 43, 44],
  "values": {
    "category_id": [[4, 7]]
  }
}
```

Different values per record, in one transaction, on Odoo 19 and later:

```json
{
  "model": "res.partner",
  "updates": [
    {"id": 42, "values": {"phone": "+1 555 0100"}},
    {"id": 43, "values": {"phone": "+1 555 0101"}}
  ]
}
```

The second form uses Odoo's `web_save_multi`. In standard mode, the Odoo MCP module must
allow that method.

##### `delete_record`

```json
{
  "model": "res.partner",
  "record_id": 42
}
```

#### Files and attachments

##### `read_attachment`

Read a file: an attachment or a binary field such as an image. Pass exactly one of `uri`
(an `odoo://attachment/{id}` or `odoo://{model}/record/{id}/{field}` URI from a tool
result) or `attachment_id`. The result depends on the file:

- text files: their text, up to 100,000 characters
- PDF and Office files: the text Odoo extracted from them (Odoo extracts PDF text only
  with the `attachment_indexation` module)
- PNG, JPEG, GIF and WebP images up to 256 KB: the image itself
- anything else: a download link for a person logged in to Odoo

```json
{
  "uri": "odoo://res.partner/record/42/image_1920"
}
```

Most chat clients never read MCP resources by themselves, so this tool is the way for the
model to see a file.

##### `list_record_attachments`

List the files attached to a record, newest first, with name, mimetype, size, date and an
`odoo://attachment/{id}` URI each. Files behind binary fields such as `image_1920` are
not listed, because `get_record` returns those as URIs.

```json
{
  "model": "res.partner",
  "record_id": 42
}
```

##### `upload_attachment`

Attach a file to a record. `data` is the file as plain base64, at most about 2.9 MB after
decoding. Odoo detects the mimetype when `mimetype` is not given. The result carries the
new attachment's ID and its `odoo://attachment/{id}` URI. To show the file in the
chatter, pass the ID to `post_message` as `attachment_ids`.

```json
{
  "model": "res.partner",
  "record_id": 42,
  "name": "contract.pdf",
  "data": "JVBERi0xLjQK...",
  "mimetype": "application/pdf"
}
```

In standard mode, the user needs write access on the record's model and create access on
`ir.attachment`.

#### Collaboration

##### `post_message`

Post a message to a record's chatter (`mail.thread`). `subtype="note"` (default) is an
internal log; `subtype="comment"` notifies followers. Set `body_is_html=true` for HTML
markup. Optional `subject` sets a message subject line; optional `partner_ids` and
`attachment_ids` reference existing partners and attachments.

```json
{
  "model": "res.partner",
  "record_id": 42,
  "body": "Called customer, will follow up Tuesday"
}
```

```json
{
  "model": "sale.order",
  "record_id": 17,
  "body": "<p>Shipping confirmed for Monday</p>",
  "subtype": "comment",
  "body_is_html": true
}
```

#### Workflow escape hatch

##### `call_model_method`

Generic XML-RPC `execute_kw` escape hatch — invokes public **business** methods, for
workflow actions not covered by CRUD (post invoice, confirm sale order, validate picking,
etc.). Available **only** when both `ODOO_YOLO=true` (full YOLO) and
`ODOO_MCP_ENABLE_METHOD_CALLS=true` are set; otherwise the tool is not registered. Only
public ASCII Python identifiers are accepted as method names — dotted, dashed, whitespace,
non-ASCII, and `_`-prefixed names are rejected.

Some calls are blocked for safety even in full YOLO mode:

- **`ir.actions.*` / `ir.cron` models** — their methods run with elevated privileges
  (server actions, scheduled jobs)
- **`run` / `method_direct_trigger`** on any model — same escalation risk via proxies
- **ORM CRUD/data-access primitives** (`create`, `write`, `unlink`, `read`, `search*`,
  `copy`, `sudo`, ...) — use the dedicated tools instead
- **`web_*` methods** — the web-client data-access family

List results are truncated to 100 items.

Over JSON-2 (Odoo 19 and later in YOLO mode with an API key, or
`ODOO_RPC_TRANSPORT=json2`), Odoo takes named arguments only. `arguments` can then hold
only the record IDs, as its first item. Pass every other argument in `keyword_arguments`,
by its parameter name, for example `{"partner_ids": [3]}`.

> [!WARNING]
> This tool can still invoke destructive workflow methods (e.g. `button_draft`,
> `action_cancel`, `toggle_active`, custom methods). Enable only in trusted environments
> where you accept the blast radius. Odoo's record rules and ACLs still apply for the
> authenticated user.

```json
{
  "model": "account.move",
  "method": "action_post",
  "arguments": [[42]]
}
```

```json
{
  "model": "sale.order",
  "method": "action_confirm",
  "arguments": [[7]],
  "keyword_arguments": {"context": {"lang": "en_US"}}
}
```

### Field selection and per-call context

#### Smart field selection

When you omit the `fields` parameter (or set it to `null`), the server automatically
selects the most relevant fields for each model using a scoring algorithm:

- **Essential fields** like `id`, `name`, `display_name`, and `active` are always included
- **Business-relevant fields** (state, amount, email, phone, partner, etc.) are prioritized
- **Technical fields** (message threads, activity tracking, website metadata) are excluded
- **Expensive fields** (binary, HTML, large text) are skipped; computed non-stored fields
  are deprioritized
- **Credential-like fields** (names ending in `*password`, `*_pass` like `smtp_pass`,
  `passwd`, `*secret`, `*_token`, `*apikey`, or a `*_key` compound such as
  `api_key`/`secret_key`) are excluded from smart defaults and withheld from
  `["__all__"]` reads with an explanatory note — requesting such a field explicitly by
  name still returns it

The default limit is 15 fields per request. Responses include metadata showing which
fields were returned and how many total fields are available. You can adjust the limit
with `ODOO_MCP_MAX_SMART_FIELDS` or bypass it entirely with `fields: ["__all__"]`.

If Odoo refuses a field to the connected user, for example an accounting total on a
contact for a user without accounting rights, a smart-default or `["__all__"]` read
leaves that field out. The response lists it in `skipped_fields` and in the note. A read
with an explicit field list still fails with the access error.

#### Per-call context

`search_records`, `get_record`, `aggregate_records`, `create_record`, `create_records`,
`update_record` and `update_records` take an optional `context` object. It accepts four
keys:

| Key | Effect |
|---|---|
| `allowed_company_ids` | The companies of the call. The first one is the active company, so company-dependent fields such as `standard_price` read and write its value. |
| `lang` | The language of labels and translated values. A language that Odoo has not installed is refused. On Odoo 16 and 17 the server checks this itself; in standard mode that needs `res.partner` or `res.lang` enabled for MCP, otherwise only `en_US` is accepted. |
| `tz` | The timezone of the call. |
| `active_test` | `false` includes archived records in searches. |

The tool refuses any other key and names it. Each company must be one of the user's
companies, and one of `ODOO_ALLOWED_COMPANIES` when that is set. The context applies to
the search, the count, the read, the existence check and the read-back after a write.

```json
{
  "model": "product.product",
  "record_id": 42,
  "values": {"standard_price": 12.5},
  "context": {"allowed_company_ids": [5]}
}
```

### Resource URIs

Beyond tools, the server exposes Odoo data as resource URIs:

| URI Pattern | Description |
|------------|-------------|
| `odoo://{model}/record/{id}` | Retrieve a specific record by ID |
| `odoo://{model}/search` | Search records with default settings (the first `ODOO_MCP_DEFAULT_LIMIT` records, 25 by default) |
| `odoo://{model}/count` | Count all records in a model |
| `odoo://{model}/fields` | Get field definitions and metadata for a model |
| `odoo://{model}/record/{id}/{field}` | Fetch a binary/image field from a record, served with the correct mimeType |
| `odoo://attachment/{id}` | Fetch an `ir.attachment` by ID (url-type attachments return their URL as text) |

**Examples:**
- `odoo://res.partner/record/1` — Get partner with ID 1
- `odoo://product.product/search` — List the first products
- `odoo://res.partner/count` — Count all partners
- `odoo://product.product/fields` — Show all fields for products
- `odoo://res.partner/record/1/image_128` — Get partner 1's avatar image
- `odoo://attachment/42` — Download attachment 42

Populated binary fields in `get_record`/`search_records` results are returned as these
resource URIs instead of inline base64 — read the URI to retrieve the actual bytes. The
bytes come from `resources/read`, or from the `read_attachment` tool, which returns text
files (up to 1 MB) and PNG, JPEG, GIF and WebP images (up to 256 KB) inline for clients
that do not read resources.

Record and search resource reads withhold credential-like fields the same way the tools'
bulk reads do — to read such a field, request it explicitly by name via the tools'
`fields` parameter.

Binary and attachment reads are served whole, up to `ODOO_MCP_MAX_BINARY_SIZE`
(default 50 MB). The size is checked before the payload is fetched, so an oversized field
or attachment is refused with a clean error rather than buffered into a correspondingly
large response. On Odoo 20 a non-stored binary field, or a stored one whose attachment
the user cannot read, is checked only after the fetch.

> **Note:** Resource URIs don't support query parameters (like `?domain=...`). For
> filtering, pagination, and field selection, use the `search_records` tool instead.

### How it works

```
AI Assistant (Claude, Copilot, etc.)
        ↓ MCP Protocol (stdio or HTTP)
   odoomcp
        ↓ XML-RPC, or JSON-2 on Odoo 19+ in YOLO mode
   Odoo Instance
```

## 04 · Operate safely

### Security

- Always use HTTPS in production environments
- Keep your API keys secure and rotate them regularly
- Configure model access carefully — only enable necessary models
- The MCP module respects Odoo's built-in access rights and record rules
- Each API key is linked to a specific user with their permissions

#### How standard mode applies the model allowlist

In standard mode, the server checks the MCP module's model allowlist before each call. It
also checks the models that a call reaches through another model:

- Nested x2many commands in `values`. A create command (`[0, 0, {...}]`) needs create
  access on the related model, an update (`[1, id, {...}]`) needs write access, and a
  delete (`[2, id]`) needs delete access.
- On a one2many field, a link (`[4, id]`) needs write access on the related model. A
  removal (`[3, id]`, `[5]` or `[6, 0, ids]`) needs write and delete access, because Odoo
  deletes the related records when the inverse field cascades. If the related model does
  not allow deletes, update the link field of the related record instead.
- Attachments, messages, emails, followers, activities, tracking values and notifications.
  Reads return only the rows of models that allow reads. Creating, changing, moving or
  deleting a row needs write access on the model that it belongs to, also through a
  nested command such as `message_ids: [[1, id, {...}]]`.
- To create an activity, the server reads `ir.model` to find the model of `res_model_id`,
  so `ir.model` must be readable for MCP.
- Reads through a relation. A condition on a dotted path such as `user_ids.groups_id.name`,
  an `any` or `not any` condition, a name condition on an x2many field, and an `order`
  through a relation need read access on each related model that they pass through.
  Grouping by an x2many field needs read access on its related model. A condition on a
  many2one by name (`country_id ilike Germany`) stays allowed, but a dotted path into it
  (`country_id.code = DE`) needs read access on the related model.

These checks do not cover writable related fields and `_inherits` parents. For example, a
write of `email` on a user also writes to its partner. In the same way, the name, email,
phone and address of a company are fields of its partner record: if `res.partner` allows
writes, they can be changed there even when `res.company` is read-only. A many2one value
counts as part of the record that holds it: its name is returned on reads and groupings,
and you can set it to a record of a model that is not enabled. The same applies to a
many2many link (`[4, id]`, `[3, id]`, `[6, 0, ids]`). Odoo's own access rights and record
rules apply to every call.

### Troubleshooting

<details>
<summary>Connection Issues</summary>

If you're getting connection errors:
1. Verify your Odoo URL is correct and accessible
2. Check that the MCP module is installed: visit `https://your-odoo.com/mcp/health`
3. Ensure your firewall allows connections to Odoo
</details>

<details>
<summary>Authentication Errors</summary>

If authentication fails:
1. Verify your API key is active in Odoo
2. Check that the user has appropriate permissions
3. Try regenerating the API key
4. For username/password auth, ensure 2FA is not enabled
5. On Odoo 20, make sure that the API key has the `rpc` scope
6. In standard mode, make sure that the user is in the MCP User group
</details>

<details>
<summary>Model Access Errors</summary>

If you can't access certain models:
1. Go to Settings > MCP Server > Enabled Models in Odoo
2. Ensure the model is in the list and has appropriate permissions
3. Check that your user has access to that model in Odoo's security settings
</details>

<details>
<summary>"spawn uvx ENOENT" Error</summary>

This error means UV is not installed or not in your PATH:

**Solution 1: Install UV** (see [Quick start](#quick-start))

**Solution 2: macOS PATH Issue**
Claude Desktop on macOS doesn't inherit your shell's PATH. Try:
1. Quit Claude Desktop completely (Cmd+Q)
2. Open Terminal
3. Launch Claude from Terminal:
   ```bash
   open -a "Claude"
   ```

**Solution 3: Use Full Path**
Find UV location and use full path:
```bash
which uvx
# Example output: /Users/yourname/.local/bin/uvx
```

Then update your config:
```json
{
  "command": "/Users/yourname/.local/bin/uvx",
  "args": ["odoomcp"]
}
```
</details>

<details>
<summary>Database Configuration Issues</summary>

If you see "Access Denied" when listing databases:
- This is normal — some Odoo instances restrict database listing for security
- Make sure to specify `ODOO_DB` in your configuration
- The server will use your specified database without validation

Example configuration:
```json
{
  "env": {
    "ODOO_URL": "https://your-odoo.com",
    "ODOO_API_KEY": "your-key",
    "ODOO_DB": "your-database-name"
  }
}
```
Note: `ODOO_DB` is required if database listing is restricted on your server.
</details>

<details>
<summary>"SSL: CERTIFICATE_VERIFY_FAILED" Error</summary>

This error occurs when Python cannot verify SSL certificates, often on macOS or corporate
networks.

**Solution**: Add SSL certificate path to your environment configuration:

```json
{
  "env": {
    "ODOO_URL": "https://your-odoo.com",
    "ODOO_API_KEY": "your-key",
    "SSL_CERT_FILE": "/etc/ssl/cert.pem"
  }
}
```

This tells Python where to find the system's SSL certificate bundle for HTTPS
connections. The path `/etc/ssl/cert.pem` is the standard location on most systems.
</details>

<details>
<summary>Debug Mode</summary>

Enable debug logging for more information:

```json
{
  "env": {
    "ODOO_URL": "https://your-odoo.com",
    "ODOO_API_KEY": "your-key",
    "ODOO_MCP_LOG_LEVEL": "DEBUG"
  }
}
```
</details>

## 05 · Develop and contribute

### Development and testing

<details>
<summary>Running from source</summary>

```bash
# Clone the repository
git clone https://github.com/Pacoaldev/OdooMCP.git
cd odoomcp

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest --cov

# Run the server
python -m mcp_server_odoo

# Check version
python -m mcp_server_odoo --version
```
</details>

<details>
<summary>Testing with MCP Inspector</summary>

```bash
# Using uvx
npx @modelcontextprotocol/inspector uvx odoomcp

# Using local installation
npx @modelcontextprotocol/inspector python -m mcp_server_odoo
```
</details>

<details>
<summary>Test suite</summary>

```bash
# Unit tests (no Odoo needed)
uv run pytest -m "not yolo and not mcp" --cov

# YOLO integration tests (vanilla Odoo, no MCP module)
uv run pytest -m "yolo" -v

# MCP integration tests (Odoo + MCP module installed)
uv run pytest -m "mcp" -v

# All tests
uv run pytest --cov

# Run specific test categories
uv run pytest tests/test_tools.py -v
uv run pytest tests/test_server_foundation.py -v
```
</details>

### License

This project is licensed under the MIT License — see the
[LICENSE](LICENSE) file for details.

### Contributing

Contributions are very welcome! Open an issue or a pull request to discuss changes.

### Support

Thank you for using this project! If you find it helpful and would like to support my
work, kindly consider buying me a coffee. Your support is greatly appreciated!

<a href="https://ko-fi.com/pacoaldev" target="_blank"><img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Buy Me a Coffee at ko-fi.com" style="height: 36px !important;" ></a>

And do not forget to give the project a star if you like it! :star:
