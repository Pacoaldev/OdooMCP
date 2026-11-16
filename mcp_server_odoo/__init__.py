"""MCP Server for Odoo - Model Context Protocol server for Odoo ERP systems."""

__version__ = "1.0.1"
__author__ = "Paco López (Pacoaldev)"
__license__ = "MIT"

from .access_control import AccessControlError, AccessController, ModelPermissions
from .config import OdooConfig, load_config
from .odoo_connection import OdooConnection, OdooConnectionError, create_connection
from .server import OdooMCPServer

__all__ = [
    "OdooMCPServer",
    "OdooConfig",
    "load_config",
    "OdooConnection",
    "OdooConnectionError",
    "create_connection",
    "AccessController",
    "AccessControlError",
    "ModelPermissions",
    "__version__",
]
