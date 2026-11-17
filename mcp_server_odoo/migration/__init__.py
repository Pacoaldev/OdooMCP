"""Odoo series migration support for custom modules.

Contents:
    rules      -- the versioned rule registry (id, severity, message, doc)
    scanner    -- read-only scanners that apply the rules to a module tree
"""

from .rules import REGISTRY, Rule, get_rule, rule_inventory, rules_for
from .scanner import AddonsScan, Finding, ModuleScan, scan_addons, scan_module

__all__ = [
    "REGISTRY",
    "Rule",
    "get_rule",
    "rules_for",
    "rule_inventory",
    "Finding",
    "ModuleScan",
    "AddonsScan",
    "scan_module",
    "scan_addons",
]
