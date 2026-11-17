"""Tests for the migration_* tools (Odoo 19 -> 20 migration support).

The migration tools are filesystem-only: they never talk to Odoo. These tests
drive the tool handler methods and the MCPServer registration surface.
"""

from unittest.mock import MagicMock

import pytest
from mcp.server.mcpserver import MCPServer

from mcp_server_odoo.access_control import AccessController
from mcp_server_odoo.config import OdooConfig
from mcp_server_odoo.error_handling import ValidationError
from mcp_server_odoo.odoo_connection import OdooConnection
from mcp_server_odoo.tools import OdooToolHandler

# The exact set test_tools.py expects for a default config, plus the tools
# this feature adds.
BASE_TOOLS = {
    "search_records",
    "get_record",
    "get_fields",
    "get_current_context",
    "list_models",
    "create_record",
    "create_records",
    "update_record",
    "update_records",
    "delete_record",
    "post_message",
    "upload_attachment",
    "list_record_attachments",
    "read_attachment",
    "aggregate_records",
    "list_resource_templates",
}

LEGACY_MANIFEST = (
    "{'name': 'Legacy', 'version': '19.0.1.0.0', 'depends': ['base'], 'installable': True}"
)
LEGACY_ACCESS_CSV = (
    "id,name,model_id,group_id/id,perm_read,perm_write,perm_create,perm_unlink\n"
    "access_legacy_user,legacy.user,model_legacy,,1,1,1,0\n"
)
MODERN_ACCESS_CSV = (
    "id,name,model_id,group_id/id,operation,domain\n"
    "access_legacy_user,legacy.user,model_legacy,,crud,\n"
)


def write_module(
    addons_dir,
    name="legacy_module",
    version="19.0.1.0.0",
    access_csv_name="ir.model.access.csv",
    access_csv=LEGACY_ACCESS_CSV,
):
    """Create a minimal module directory under ``addons_dir``."""
    module = addons_dir / name
    module.mkdir(parents=True)
    (module / "__manifest__.py").write_text(
        "{'name': 'Legacy', 'version': '%s', 'depends': ['base'], 'installable': True}"
        % version,
        encoding="utf-8",
    )
    if access_csv_name:
        security = module / "security"
        security.mkdir()
        (security / access_csv_name).write_text(access_csv, encoding="utf-8")
    return module


class MigrationFixtureMixin:
    @pytest.fixture
    def mock_app(self):
        app = MagicMock(spec=MCPServer)
        app._tools = {}

        def tool_decorator(**kwargs):
            def decorator(func):
                app._tools[func.__name__] = func
                return func

            return decorator

        app.tool = tool_decorator
        return app

    @pytest.fixture
    def mock_connection(self):
        connection = MagicMock(spec=OdooConnection)
        connection.is_authenticated = True
        return connection

    @pytest.fixture
    def mock_access_controller(self):
        return MagicMock(spec=AccessController)

    @pytest.fixture
    def make_handler(self, mock_app, mock_connection, mock_access_controller):
        def _make(**config_kwargs):
            config = OdooConfig(
                url="http://localhost:8069",
                api_key="test_api_key",
                database="test_db",
                **config_kwargs,
            )
            return OdooToolHandler(
                mock_app, mock_connection, mock_access_controller, config
            )

        return _make


class TestRegistration(MigrationFixtureMixin):
    def test_migration_rules_registered_by_default(self, make_handler, mock_app):
        """migration_rules lists the registry; it needs no filesystem access."""
        make_handler()

        assert "migration_rules" in mock_app._tools
        assert "migration_scan" not in mock_app._tools

    def test_migration_scan_registered_with_addons_path(self, make_handler, mock_app, tmp_path):
        make_handler(addons_path=[str(tmp_path)])

        assert set(mock_app._tools.keys()) == BASE_TOOLS | {"migration_rules", "migration_scan"}

    def test_migration_scan_absent_without_addons_path(self, make_handler, mock_app):
        """An empty ODOO_MCP_ADDONS_PATH leaves migration_scan unregistered."""
        make_handler()

        assert set(mock_app._tools.keys()) == BASE_TOOLS | {"migration_rules"}


class TestMigrationScan(MigrationFixtureMixin):
    async def test_scan_reports_findings_from_configured_addons_path(
        self, make_handler, tmp_path
    ):
        write_module(tmp_path)

        handler = make_handler(addons_path=[str(tmp_path)])
        result = await handler._handle_migration_scan_tool()

        assert result["target"] == "20.0"
        assert result["roots"] == [str(tmp_path)]
        rule_ids = {finding["rule_id"] for module in result["modules"] for finding in module["findings"]}
        assert "ODOO20001" in rule_ids  # pre-20.0 manifest version
        assert "ODOO20002" in rule_ids  # legacy ir.model.access.csv
        assert result["counts"]["error"] >= 1

    async def test_scan_without_addons_path_is_refused(self, make_handler):
        """Calling the handler with no addons path fails cleanly, not with a crash."""
        handler = make_handler()

        with pytest.raises(ValidationError, match="ODOO_MCP_ADDONS_PATH"):
            await handler._handle_migration_scan_tool()

    async def test_scan_reports_missing_root(self, make_handler, tmp_path):
        missing = tmp_path / "no-such-addons"
        handler = make_handler(addons_path=[str(missing)])

        result = await handler._handle_migration_scan_tool()

        assert result["modules"] == []
        assert any("root does not exist" in error["error"] for error in result["errors"])

    async def test_scan_modules_filter_scans_only_named_modules(self, make_handler, tmp_path):
        write_module(tmp_path, name="alpha")
        write_module(tmp_path, name="beta")
        handler = make_handler(addons_path=[str(tmp_path)])

        result = await handler._handle_migration_scan_tool(modules=["alpha"])

        assert [module["module"] for module in result["modules"]] == ["alpha"]

    async def test_scan_clean_module_reports_no_findings(self, make_handler, tmp_path):
        """A module already ported to Odoo 20 produces no findings."""
        write_module(
            tmp_path,
            name="modern_module",
            version="20.0.1.0.0",
            access_csv_name="ir.access.csv",
            access_csv=MODERN_ACCESS_CSV,
        )
        handler = make_handler(addons_path=[str(tmp_path)])

        result = await handler._handle_migration_scan_tool()

        assert result["counts"] == {"error": 0, "warning": 0, "info": 0, "modules": 1}

    async def test_scan_uses_configured_migration_target(self, make_handler, tmp_path):
        """A 20.0 manifest is flagged when the configured target is 21.0."""
        write_module(tmp_path, version="20.0.1.0.0")
        handler = make_handler(addons_path=[str(tmp_path)], migration_target="21.0")

        result = await handler._handle_migration_scan_tool()

        assert result["target"] == "21.0"
        rule_ids = {
            finding["rule_id"] for module in result["modules"] for finding in module["findings"]
        }
        assert "ODOO20001" in rule_ids

    async def test_scan_target_parameter_overrides_config(self, make_handler, tmp_path):
        write_module(tmp_path, version="20.0.1.0.0")
        handler = make_handler(addons_path=[str(tmp_path)])

        result = await handler._handle_migration_scan_tool(target="21.0")

        assert result["target"] == "21.0"
        rule_ids = {
            finding["rule_id"] for module in result["modules"] for finding in module["findings"]
        }
        assert "ODOO20001" in rule_ids

    async def test_scan_target_parameter_validates_shape(self, make_handler, tmp_path):
        handler = make_handler(addons_path=[str(tmp_path)])

        with pytest.raises(ValidationError, match="target"):
            await handler._handle_migration_scan_tool(target="not-a-series")


class TestMigrationRules(MigrationFixtureMixin):
    async def test_rules_lists_the_registry(self, make_handler):
        handler = make_handler()

        result = await handler._handle_migration_rules_tool()

        ids = [rule["id"] for rule in result["rules"]]
        assert "ODOO20001" in ids
        for rule in result["rules"]:
            assert {"id", "title", "severity", "applies_to", "message", "doc"} <= set(rule)

    async def test_rules_echo_configured_target(self, make_handler):
        handler = make_handler(migration_target="21.0")

        result = await handler._handle_migration_rules_tool()

        assert result["target"] == "21.0"
        assert result["count"] == len(result["rules"])
