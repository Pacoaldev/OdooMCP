# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Unreleased - 2026-11-15

### Changed
- CI: disabled the `mcp-integration-test` job until the Odoo MCP module lives in an accessible repository; `build` already tolerates the skipped job.
- Restructured the README documentation (English and Spanish) and updated the project descriptions.

### Fixed
- Heading hierarchy and Spanish errata in both READMEs.
- Windows-only test failures: temporary log-file deletion in `test_setup_logging` (an open file handle blocked `os.unlink`) and the unreachable-connection message asserted by `test_nothing_listening_is_unreachable` (Windows reports a dead port as a connect timeout, not a refusal).

### Added
- MCP server connecting AI assistants to Odoo ERP over XML-RPC and JSON-2 transports.
- Tools for searching, reading, creating, updating and deleting Odoo records, including batch writes, attachments and binary file reads.
- `odoo://` resource URIs for models, records, search results and attachments.
- Access control with per-model permissions and field-level security.
- Error sanitization and configurable structured logging.
- Docker image for containerized deployments.
- CI, Docker and PyPI publishing workflows.

### Changed
- Rebranded the project from `odoo-minion-mcp` to `odoomcp`.
- License changed to MIT.

[Unreleased]: https://github.com/Pacoaldev/OdooMCP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Pacoaldev/OdooMCP/releases/tag/v1.0.0
