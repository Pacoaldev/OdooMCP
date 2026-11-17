# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Odoo 19 → 20 migration assistant in the Python MCP server: `migration_rules` and `migration_scan` tools, versioned rules registry, and static scanners for manifests, `ir.access.csv`, and Python AST patterns.
- Isolated Odoo 20 Docker stack (`docker-compose.odoo20.yml`, `Dockerfile.odoo20`) on host port **8070**, side by side with the Odoo 19 dev stack.
- Addon support for **mcp-scoped** API keys on Odoo 20 (wizard `scope_mode`, extended `scope` selection, tighter `res.users.apikeys` read rule for MCP users).

### Changed
- `mcp_server` addon manifest and security adapted for Odoo **20.0** (`ir.access.csv`, binary fields on attachments, merged record rules).
- `README.md` / `README.es.md`: Odoo 20 Docker stack, pytest matrix, migration feature map, addon test command.

### Fixed
- Odoo 20 addon test suite: **722** tests green (`--test-tags /mcp_server`).
- Python unit suite: **1800** tests pass offline (`pytest -m "not yolo and not mcp"`); HTTP transport tests no longer hit a live Odoo when checking bind/timeout kwargs.

## [1.0.1] - 2026-11-16

### Changed
- Distribution renamed to `mcp-odoo` on PyPI: the name `odoomcp` is rejected as too similar to an existing project. The `odoomcp` console script, container entrypoint and `ghcr.io/pacoaldev/odoomcp` image are unchanged.
- Server identity renamed from `odoo-mcp-server` to `mcp-odoo`, both in the `serverInfo` reported over MCP and in the `--version` output.
- Documented install commands now use `uvx mcp-odoo`, `pip install mcp-odoo` and `pipx install mcp-odoo`.
- Documentation examples use `docker compose` (v2) instead of the deprecated `docker-compose`, and `cd OdooMCP` to match the directory created by `git clone`.

## [1.0.0] - 2026-11-16

### Added
- MCP server connecting AI assistants to Odoo ERP over XML-RPC and JSON-2 transports.
- Tools for searching, reading, creating, updating and deleting Odoo records, including batch writes, attachments and binary file reads.
- `odoo://` resource URIs for models, records, search results and attachments.
- Access control with per-model permissions and field-level security.
- Error sanitization and configurable structured logging.
- Docker image for containerized deployments.
- CI, Docker and PyPI publishing workflows.
- Persistent local Odoo 19 development stack with PostgreSQL 16, official `mcp_server` addon mount, and addon dependencies baked into `Dockerfile.odoo`.
- Development documentation for configuring local Odoo integration tests and connecting OpenCode as an MCP client.
- `AGENTS.md` guidance for local Odoo development and Spanish terminology mapping (`res.partner` vs. `res.company`).
- Pi coding agent integration: MCP server configured and tested live against Odoo 19.0.2.3.0.
  - Entry in `~/.pi/agent/mcp.json` with no embedded credentials (uses project `.env` via `load_dotenv`).
  - 17 tools + resources verified: `search_records`, `create_record`, `update_record`, `delete_record`, `aggregate_records`, attachments, and more.
  - Access control confirmed: per-model allowlist enforced (e.g., `res.users` correctly denied by Odoo configuration).
  - Live reads tested: 94 `res.partner` records (65 companies, 29 contacts) retrieved and aggregated.
- OpenCode MCP config updated to use environment variables (`{env:ODOO_API_KEY}`, `{env:ODOO_PASSWORD}`) instead of literal credentials.
- Code review of Python MCP server (`mcp_server_odoo/` modules): access control enforced on 24 write-path call sites, field-level credential withholding validated against 2475 real Odoo 19 field names, timeout retry limited to read-only allowlist.

### Changed
- Rebranded the project from `odoo-minion-mcp` to `odoomcp`.
- License changed to MIT.
- Restructured the README documentation (English and Spanish) and updated the project descriptions.
- CI: disabled the `mcp-integration-test` job until the Odoo MCP module lives in an accessible repository; `build` already tolerates the skipped job.
- Integration status: Odoo addon side (`addons/mcp_server/`, 13.7k lines) not yet audited; pytest suite not run (requires live write access authorization).

### Fixed
- Heading hierarchy and Spanish errata in both READMEs.
- Windows-only test failures: temporary log-file deletion in `test_setup_logging` (an open file handle blocked `os.unlink`) and the unreachable-connection message asserted by `test_nothing_listening_is_unreachable` (Windows reports a dead port as a connect timeout, not a refusal).

### Security
- API key rotated (old `rpc` scope key revoked, new `mcp` scope key in use).

[Unreleased]: https://github.com/Pacoaldev/OdooMCP/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/Pacoaldev/OdooMCP/releases/tag/v1.0.1
[1.0.0]: https://github.com/Pacoaldev/OdooMCP/releases/tag/v1.0.0