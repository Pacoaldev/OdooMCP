"""Read-only ``db`` service for the MCP XML-RPC surface.

Odoo 19 shipped a ``db`` RPC service in ``odoo.service.db``: a ``dispatch()``
over ``exp_*`` helpers answering at ``/xmlrpc/2/db``. Odoo 20 removed the RPC
service (only the CLI in ``odoo/cli/db.py`` and the helpers in
``odoo/modules/db.py`` remain), so the module's ``/mcp/xmlrpc/db`` endpoint had
no implementation left to proxy.

This module replaces it with a deliberately narrow, read-only dispatcher:

    list, list_dbs     -- database names on the server
    db_exist           -- whether one database exists
    server_version     -- the Odoo series, e.g. '20.0'
    list_lang          -- (code, name) pairs for translatable languages
    list_countries     -- (code, name) pairs for countries

Everything else the old service supported (create, duplicate, drop, dump,
restore, rename, change_admin_password, migrate_databases) is refused with an
explicit message. Those operations were privilege-gated in 19, Odoo removed
their RPC entry point on purpose, and re-exposing them behind an MCP route
would widen the attack surface without serving any MCP use case: the MCP
client never calls this endpoint, it discovers databases through
``/web/database/list`` and ``/xmlrpc/db``.
"""

from __future__ import annotations

import logging

import odoo.release

_logger = logging.getLogger(__name__)

# The methods this dispatcher answers. Kept public so the fault message, the
# docs and the tests all read from one list.
READ_ONLY_METHODS = (
    "list",
    "list_dbs",
    "db_exist",
    "server_version",
    "list_lang",
    "list_countries",
)

# Documented for operators reading a refusal: the write half of the old service
# that this module will not proxy.
REFUSED_METHODS = (
    "create_database",
    "duplicate_database",
    "drop",
    "dump",
    "restore",
    "rename",
    "change_admin_password",
    "migrate_databases",
)


class MethodNotSupported(KeyError):
    """Raised for a method outside the read-only subset.

    Subclasses KeyError so the XML-RPC error mapping in the controller treats it
    like the core service's ``KeyError('Method not found')``.
    """


# Odoo 20 moved the listing helpers to odoo.modules.db; Odoo 19 kept them in
# odoo.service.db. Both expose list_dbs(); only the existence check is renamed.
try:  # Odoo 20
    from odoo.modules.db import exist as _db_exist, list_dbs as _list_dbs
except ImportError:  # pragma: no cover - depends on the installed series
    from odoo.service.db import exp_db_exist as _db_exist, list_dbs as _list_dbs


def _list_lang() -> list[tuple[str, str]]:
    """Translatable languages as (code, name), sorted by name."""
    try:  # Odoo 20
        from odoo.addons.web.controllers.database import scan_languages
    except ImportError:  # pragma: no cover - depends on the installed series
        from odoo.service.db import exp_list_lang as scan_languages
    return list(scan_languages())


def _list_countries() -> list[tuple[str, str]]:
    """Countries as (code, name), sorted by name."""
    try:  # Odoo 20
        from odoo.addons.web.controllers.database import list_countries
    except ImportError:  # pragma: no cover - depends on the installed series
        from odoo.service.db import exp_list_countries as list_countries
    return list(list_countries())


def dispatch(method: str, params) -> object:
    """Answer one read-only ``db`` service call.

    Args:
        method: one of :data:`READ_ONLY_METHODS`.
        params: positional arguments as received over XML-RPC.

    Raises:
        MethodNotSupported: if the method is not read-only or does not exist.
    """
    if method in ("list", "list_dbs"):
        # 'list' accepted an optional ``document`` flag in 19; ignore it, as the
        # list of databases is the same either way.
        return _list_dbs()
    if method == "db_exist":
        return _db_exist(*params)
    if method == "server_version":
        return odoo.release.version
    if method == "list_lang":
        return _list_lang()
    if method == "list_countries":
        return _list_countries()

    if method in REFUSED_METHODS:
        raise MethodNotSupported(
            f"Method {method!r} is not available over MCP: the Odoo {odoo.release.series} "
            "RPC database service was removed and these operations are not "
            "re-exposed. Use the Odoo CLI (odoo db) or the web database manager."
        )
    raise MethodNotSupported(f"Method not found: {method}")
