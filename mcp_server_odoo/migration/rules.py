"""Odoo series migration rules for custom modules.

The rules are data, not code. A scanner walks a file, asks the registry which
rules apply to that kind of file for the configured target series, and evaluates
each rule's matcher. Adding a rule is therefore a registry entry plus a test,
with no change to the scanners.

Severity is about what happens to the module, not about style:

* ``error``   -- the module fails to install, or the call no longer exists.
* ``warning`` -- it installs but behaviour silently changes, or the API is
  deprecated and scheduled for removal.
* ``info``    -- cosmetic or asset-only.

Provenance: the Odoo 20.0 documentation (``developer/howtos/upgrade_custom_db``
and the ORM reference) plus community porting checklists. Each entry records
what was observed; the docker-based check in ``tests/`` is what confirms a rule
against a real ``odoo:20.0`` before it is trusted. A rule that cannot be
confirmed there must not be promoted to ``error``.

Rule ids are stable: they appear in tool output, docs and tests. Never renumber
an existing id; retire it instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

Severity = Literal["error", "warning", "info"]
AppliesTo = Literal["manifest", "security_csv", "python", "xml"]


@dataclass(frozen=True)
class Match:
    """Declarative description of what a rule looks for.

    Exactly one ``kind`` is meaningful per rule. The fields are flat rather
    than a union of dataclasses so the registry stays readable as a table.
    """

    kind: Literal[
        "manifest_version",  # expected_prefix
        "csv_name",  # forbidden
        "call",  # name: attribute called as a method
        "call_attr",  # name + receiver: <receiver>.<name>(...)
        "kwarg",  # name: keyword argument in a call
        "definition",  # name: function/method definition
        "text",  # regex: raw source match
    ]
    name: str = ""
    receiver: str = ""
    regex: str = ""
    forbidden: str = ""
    expected_prefix: str = ""

    def compiled(self) -> Optional[re.Pattern[str]]:
        if self.kind == "text" and self.regex:
            return re.compile(self.regex)
        return None


@dataclass(frozen=True)
class Rule:
    """A single migration check."""

    id: str
    title: str
    severity: Severity
    applies_to: AppliesTo
    message: str
    doc: str
    match: Match
    # First Odoo series where the change bites. A rule introduced in 20.0 is
    # still reported when targeting 21.0.
    introduced: str = "20.0"
    # Last series where the old API still works, when known.
    removed_in: Optional[str] = None


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

MANIFEST_VERSION = Rule(
    id="ODOO20001",
    title="Manifest declares a pre-20.0 series",
    severity="error",
    applies_to="manifest",
    message=(
        "'version' must start with the target series ('20.0.'). Odoo does not "
        "fail loudly otherwise: it logs 'The module ... has an incompatible "
        "version, setting installable=False', leaves the module out of the "
        "Apps list and exits with status 0."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/cli.html",
    match=Match(kind="manifest_version", expected_prefix="20.0"),
)


# --------------------------------------------------------------------------
# Security files
# --------------------------------------------------------------------------

SECURITY_CSV_NAME = Rule(
    id="ODOO20002",
    title="Old ir.model.access.csv security file",
    severity="error",
    applies_to="security_csv",
    message=(
        "security/ir.model.access.csv was replaced by security/ir.access.csv. "
        "The old columns (perm_read/perm_write/perm_create/perm_unlink) are "
        "replaced by a single 'operation' column ('r', 'cru', 'crud') plus an "
        "optional 'domain'. Keeping the old file fails at install with "
        "KeyError: 'ir.model.access'."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/security.html",
    match=Match(kind="csv_name", forbidden="ir.model.access.csv"),
)


# --------------------------------------------------------------------------
# Python
# --------------------------------------------------------------------------

FIELD_AGGREGATOR = Rule(
    id="ODOO20003",
    title="Field attribute group_operator",
    severity="warning",
    applies_to="python",
    message=(
        "fields.*(group_operator='avg') is now fields.*(aggregator='avg'). "
        "group_operator stopped being a known parameter: the field logs a "
        "warning at startup and silently falls back to the default aggregate, "
        "so totals are wrong rather than absent."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="kwarg", name="group_operator"),
    introduced="20.0",
    removed_in="20.0",
)

ENV_CLEAR = Rule(
    id="ODOO20004",
    title="env.clear() cache reset",
    severity="warning",
    applies_to="python",
    message=(
        'env.clear() carries @deprecated("Since 20.0, use transaction.clear or '
        'transaction.reset"). It still clears the cache, but the deprecation '
        "is scheduled to become a removal."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="call_attr", receiver="env", name="clear"),
)

CHECK_FIELD_ACCESS = Rule(
    id="ODOO20005",
    title="Private _check_field_access",
    severity="warning",
    applies_to="python",
    message=(
        "_check_field_access(field, op) became the public "
        "check_field_access(field, op). The private name still works with a "
        "deprecation warning."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="call", name="_check_field_access"),
)

CHECK_ACCESS_OVERRIDE = Rule(
    id="ODOO20006",
    title="Overriding _check_access",
    severity="warning",
    applies_to="python",
    message=(
        "Custom access rules now override _access_domain(operation) instead of "
        "_check_access(operation). The old hook still fires with a deprecation "
        "warning, so a module that overrides both can apply its rules twice."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="definition", name="_check_access"),
)

CHECK_ACCESS_RIGHTS = Rule(
    id="ODOO20007",
    title="check_access_rights / check_access_rule",
    severity="error",
    applies_to="python",
    message=(
        "check_access_rights and check_access_rule are gone from the ORM: they "
        "are not defined anywhere in Odoo 20 core. Call check_access(operation) "
        "instead, or _access_domain/has_access for the finer-grained cases."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="call", name="check_access_rights"),
)

CONFIG_PARAMETER_TYPED = Rule(
    id="ODOO20008",
    title="ir.config_parameter.get_param / set_param",
    severity="error",
    applies_to="python",
    message=(
        "get_param and set_param are gone. Use the typed API: get_str, "
        "get_int, get_bool, get_float and the matching set_* methods. Calling "
        "the old names raises AttributeError at runtime, after install."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="call", name="get_param"),
)

ATTACHMENT_DATAS = Rule(
    id="ODOO20009",
    title="ir.attachment.datas",
    severity="error",
    applies_to="python",
    message=(
        "ir.attachment.datas was removed. Read 'raw' instead; 'db_datas' "
        "remains as the stored-storage column."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="text", regex=r"\.datas\b"),
)

BINARY_B64DECODE = Rule(
    id="ODOO20010",
    title="base64 decoding of a binary field",
    severity="warning",
    applies_to="python",
    message=(
        "Binary fields hold BinaryValue/BinaryBytes (.content, .decode(), "
        ".to_base64()), not base64 text. base64.b64decode(record['image_1920']) "
        "now raises TypeError, and convert_to_read returns "
        "{'content', 'filename', 'size'} instead of a string."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="call", name="b64decode"),
)

COPY_TRANSLATIONS = Rule(
    id="ODOO20011",
    title="copy_translations()",
    severity="error",
    applies_to="python",
    message=(
        "copy_translations() is gone. Translations are assigned as a dict on "
        "the field (record.name = {'en_US': 'Chair', 'fr_FR': 'Chaise'}), and "
        "copy_data carries them that way."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="call", name="copy_translations"),
)

TRACKING_VALUE_IDS = Rule(
    id="ODOO20012",
    title="mail.tracking.value / tracking_value_ids",
    severity="warning",
    applies_to="python",
    message=(
        "The tracking model and the tracking_value_ids field moved to the "
        "mail_tracking module. Modules touching them must depend on it "
        "explicitly instead of relying on mail."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="text", regex=r"\btracking_value_ids\b"),
)

REQUEST_WEBSITE = Rule(
    id="ODOO20013",
    title="request.website outside a web request",
    severity="warning",
    applies_to="python",
    message=(
        "A minimal 'website' model now lives in base and env.website returns "
        "the current one. Reaching for request.website fails in cron jobs and "
        "other non-request contexts."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/orm.html",
    match=Match(kind="text", regex=r"\brequest\.website\b"),
)


# --------------------------------------------------------------------------
# XML / QWeb
# --------------------------------------------------------------------------

FONT_AWESOME = Rule(
    id="ODOO20014",
    title="Font Awesome icon classes",
    severity="info",
    applies_to="xml",
    message=(
        "The web client replaced Font Awesome with Material Symbols. 'fa fa-*' "
        "classes in QWeb views render as empty boxes and need the equivalent "
        "Material Symbols class."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/frontend.html",
    match=Match(kind="text", regex=r"\bfa\s+fa-[a-z0-9-]+"),
)

IR_RULE_REMOVED = Rule(
    id="ODOO20015",
    title="ir.rule model was removed",
    severity="error",
    applies_to="xml",
    message=(
        "ir.rule was merged into ir.access. Record rules are now ir.access "
        "records with model_id, group_id, operation and a 'domain' field; the "
        "perm_read/perm_write/perm_create/perm_unlink flags and domain_force "
        'are gone. A view or data file still declaring model="ir.rule" fails '
        "to load."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/security.html",
    match=Match(kind="text", regex=r'model=["\']ir\.rule["\']'),
)

ACCESS_CSV_MISSING_COLUMN = Rule(
    id="ODOO20016",
    title="ir.access.csv is missing a required column",
    severity="error",
    applies_to="security_csv",
    message=(
        "An Odoo 20 ir.access.csv needs exactly the columns id, name, model_id, "
        "group_id/id, operation, domain. Note that model_id and group_id/id "
        "are bare values, without the historic :id suffix."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/security.html",
    match=Match(kind="csv_name", forbidden="ir.access.csv"),
)

ACCESS_CSV_BAD_OPERATION = Rule(
    id="ODOO20017",
    title="ir.access.csv has an invalid operation",
    severity="error",
    applies_to="security_csv",
    message=(
        "'operation' is a subset of 'crud', for example 'r', 'cru' or 'crud'. "
        "Any other value is rejected when the record is created, so the "
        "module fails to install."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/security.html",
    match=Match(kind="csv_name", forbidden="ir.access.csv"),
)

ACCESS_CSV_LEGACY_COLUMNS = Rule(
    id="ODOO20018",
    title="Legacy perm_read/perm_write/perm_create/perm_unlink columns",
    severity="error",
    applies_to="security_csv",
    message=(
        "The four perm_* columns were replaced by a single 'operation' column. "
        "A CSV still carrying them installs as an ir.access record with an "
        "empty operation, which fails validation."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/security.html",
    match=Match(kind="csv_name", forbidden="perm_read"),
)

CORS_MAX_AGE_MOVED = Rule(
    id="ODOO20019",
    title="CORS_MAX_AGE moved out of odoo.http",
    severity="error",
    applies_to="python",
    message=(
        "CORS_MAX_AGE is no longer exported from odoo.http; in Odoo 20 it "
        "lives in odoo.http.dispatcher. 'from odoo.http import CORS_MAX_AGE' "
        "raises ImportError while the module is being loaded, which aborts the "
        "whole registry and takes the database down, not just the module."
    ),
    doc="https://www.odoo.com/documentation/20.0/developer/reference/http.html",
    match=Match(kind="text", regex=r"from\s+odoo\.http\s+import\s+[^\n]*\bCORS_MAX_AGE"),
)

# Rules whose matcher is structural rather than declarative: the scanner
# enforces them from the file contents, and looks them up here so id, message
# and severity stay in one place. Declared after their definitions.
STRUCTURAL_RULE_IDS: tuple[str, ...] = (
    ACCESS_CSV_MISSING_COLUMN.id,
    ACCESS_CSV_BAD_OPERATION.id,
    ACCESS_CSV_LEGACY_COLUMNS.id,
    IR_RULE_REMOVED.id,
)


REGISTRY: tuple[Rule, ...] = (
    MANIFEST_VERSION,
    SECURITY_CSV_NAME,
    FIELD_AGGREGATOR,
    ENV_CLEAR,
    CHECK_FIELD_ACCESS,
    CHECK_ACCESS_OVERRIDE,
    CHECK_ACCESS_RIGHTS,
    CONFIG_PARAMETER_TYPED,
    ATTACHMENT_DATAS,
    BINARY_B64DECODE,
    COPY_TRANSLATIONS,
    TRACKING_VALUE_IDS,
    REQUEST_WEBSITE,
    FONT_AWESOME,
    IR_RULE_REMOVED,
    ACCESS_CSV_MISSING_COLUMN,
    ACCESS_CSV_BAD_OPERATION,
    ACCESS_CSV_LEGACY_COLUMNS,
    CORS_MAX_AGE_MOVED,
)

RULES_BY_ID: dict[str, Rule] = {rule.id: rule for rule in REGISTRY}


def series_key(series: str) -> tuple[int, ...]:
    """Turn '20.0' into (20, 0) so series compare numerically."""
    return tuple(int(part) for part in series.split("."))


def rules_for(applies_to: str, target: str = "20.0") -> list[Rule]:
    """Rules of one file kind that apply to a target series.

    A rule introduced in 20.0 still applies when targeting 21.0: the whole
    point is to flag code written for an older series.
    """
    target_key = series_key(target)
    return [
        rule
        for rule in REGISTRY
        if rule.applies_to == applies_to and series_key(rule.introduced) <= target_key
    ]


def get_rule(rule_id: str) -> Rule:
    """Look up a rule by id.

    Raises:
        KeyError: If the id is not in the registry.
    """
    try:
        return RULES_BY_ID[rule_id]
    except KeyError:
        raise KeyError(f"Unknown migration rule: {rule_id}") from None


def rule_inventory() -> list[dict[str, str]]:
    """Every rule as a plain dict, for the explain tool."""
    return [
        {
            "id": rule.id,
            "title": rule.title,
            "severity": rule.severity,
            "applies_to": rule.applies_to,
            "introduced": rule.introduced,
            "removed_in": rule.removed_in or "",
            "message": rule.message,
            "doc": rule.doc,
        }
        for rule in REGISTRY
    ]
