# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-15

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
