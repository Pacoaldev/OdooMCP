"""Static scanners for the Odoo migration rules.

Each scanner walks one kind of file, asks :mod:`mcp_server_odoo.migration.rules`
which rules apply, and reports matches. The matcher kinds are evaluated here,
which keeps the registry declarative and the matching in one place.

Scanners only read. They never import the scanned module, never execute it and
never connect to Odoo: a module that does not run yet is exactly the module
that needs scanning.
"""

from __future__ import annotations

import ast
import csv
import io
import logging
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .rules import Match, Rule, get_rule, rules_for

logger = logging.getLogger(__name__)

MANIFEST_NAME = "__manifest__.py"
SECURITY_DIR = "security"
# Directories that never hold module source: skipping them keeps a scan of a
# full addons tree linear instead of quadratic on vendored dependencies.
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
}

# Odoo 20 ir.access.csv: the permitted 'operation' values, from the core
# CRUD_SELECTION in addons/base/models/ir_access.py.
VALID_OPERATIONS = {
    "crud",
    "cru",
    "crd",
    "cud",
    "rud",
    "cr",
    "cu",
    "cd",
    "ru",
    "rd",
    "ud",
    "c",
    "r",
    "u",
    "d",
}
ACCESS_CSV_NAME = "ir.access.csv"
LEGACY_ACCESS_CSV_NAME = "ir.model.access.csv"
ACCESS_CSV_COLUMNS = ("id", "name", "model_id", "group_id/id", "operation", "domain")

# Files whose contents are data, not importable source.
TEXT_SUFFIXES = {".xml", ".py", ".csv", ".js", ".scss", ".css", ".html"}


@dataclass
class Finding:
    """One rule violation at one location."""

    rule_id: str
    severity: str
    title: str
    message: str
    doc: str
    module: str
    path: str
    line: int = 0
    snippet: str = ""

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "doc": self.doc,
            "module": self.module,
            "path": self.path,
            "line": self.line,
            "snippet": self.snippet,
        }


@dataclass
class ModuleScan:
    """Result of scanning one module directory."""

    module: str
    path: str
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    # Files a rule could not be evaluated against (unparseable Python, bad
    # CSV). Reported instead of swallowed: a scan that silently skips a broken
    # file is worse than no scan.
    errors: list[dict] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        counter = Counter(finding.severity for finding in self.findings)
        return {
            "error": counter.get("error", 0),
            "warning": counter.get("warning", 0),
            "info": counter.get("info", 0),
        }

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "path": self.path,
            "files_scanned": self.files_scanned,
            "counts": self.counts,
            "findings": [finding.to_dict() for finding in self.findings],
            "errors": self.errors,
        }


@dataclass
class AddonsScan:
    """Result of scanning one or more addons roots."""

    target: str
    roots: list[str]
    modules: list[ModuleScan] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        total = Counter()
        for module in self.modules:
            total.update(module.counts)
        return {
            "error": total.get("error", 0),
            "warning": total.get("warning", 0),
            "info": total.get("info", 0),
            "modules": len(self.modules),
        }

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "roots": self.roots,
            "counts": self.counts,
            "skipped": self.skipped,
            "errors": self.errors,
            "modules": [module.to_dict() for module in self.modules],
        }


# --------------------------------------------------------------------------
# Module discovery
# --------------------------------------------------------------------------


def is_module_dir(path: Path) -> bool:
    """A module directory is one holding a __manifest__.py."""
    return (path / MANIFEST_NAME).is_file()


def discover_modules(root: Path) -> tuple[list[Path], list[str]]:
    """Find module directories under ``root``.

    A root may itself be a module, a directory of modules, or an addons tree
    with modules several levels down. Returns ``(found, skipped)``, where
    ``skipped`` names directories pruned because they are not traversable.
    """
    if is_module_dir(root):
        return [root], []

    found: list[Path] = []
    skipped: list[str] = []
    for current, dirnames, _ in os.walk(root):
        current_path = Path(current)
        if current_path == root:
            pruned = [name for name in dirnames if name in SKIP_DIRS]
            skipped.extend(str(current_path / name) for name in pruned)
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
            continue
        if is_module_dir(current_path):
            # Nested addons trees exist, but a module containing another
            # module is a packaging mistake, not two modules to scan twice.
            found.append(current_path)
            skipped.extend(str(current_path / name) for name in dirnames)
            dirnames[:] = []
            continue
        pruned = [name for name in dirnames if name in SKIP_DIRS]
        skipped.extend(str(current_path / name) for name in pruned)
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
    return sorted(found), skipped


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


def _manifest_dict(text: str) -> Optional[dict]:
    """Parse __manifest__.py.

    The file is a Python dict literal, so literal_eval is enough and much
    safer than importing the module. It is also often written with a
    ``# noqa`` or a small expression, so a failure is reported, not raised.
    """
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None
    return value if isinstance(value, dict) else None


def scan_manifest(path: Path, module: str, target: str) -> tuple[list[Finding], list[dict]]:
    """Apply manifest rules to one __manifest__.py."""
    findings: list[Finding] = []
    errors: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    manifest = _manifest_dict(text)

    if manifest is None:
        errors.append(
            {
                "path": str(path),
                "error": "manifest is not a Python dict literal; rules skipped",
            }
        )
        return findings, errors

    version = manifest.get("version")
    for rule in rules_for("manifest", target):
        if rule.match.kind != "manifest_version":
            continue
        # The rule message says 'version' must start with the TARGET series, so
        # the configured target governs here — not a literal series baked into
        # the scanner, which would let a 20.0 manifest pass a 21.0 scan. A
        # manifest may declare a bare '2.3.0' and let Odoo prefix the series,
        # so a version with no series part is accepted either way.
        rendered = str(version) if version is not None else ""
        has_series = rendered.startswith(target + ".")
        looks_prefixed = bool(re.match(r"^\d+\.\d+\.", rendered))
        if not has_series and looks_prefixed:
            findings.append(
                _finding(rule, module, path, _line_of(text, "version"), f'"version": "{rendered}"')
            )

    return findings, errors


# --------------------------------------------------------------------------
# Security files
# --------------------------------------------------------------------------


def scan_security(path: Path, module: str, target: str) -> tuple[list[Finding], list[dict]]:
    """Report a legacy access CSV and validate the Odoo 20 replacement."""
    findings: list[Finding] = []
    errors: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    if path.name == LEGACY_ACCESS_CSV_NAME:
        findings.append(_finding(_LEGACY_FILE_RULE, module, path, 1, path.name))
        # The legacy columns are the concrete reason the file stops loading, so
        # report them too rather than only the filename.
        header = text.splitlines()[0] if text.splitlines() else ""
        if "perm_read" in header:
            findings.append(
                _finding(
                    _LEGACY_COLUMN_RULE,
                    module,
                    path,
                    1,
                    header.strip(),
                )
            )
        return findings, errors

    if path.name == ACCESS_CSV_NAME:
        findings.extend(_validate_access_csv(path, text, module, target, errors))

    return findings, errors


def _validate_access_csv(
    path: Path,
    text: str,
    module: str,
    target: str,
    errors: list[dict],
) -> list[Finding]:
    """Check an ir.access.csv against the Odoo 20 schema.

    A wrong column or an unknown operation fails at install time with an
    unhelpful error, so it is worth catching while scanning.
    """
    findings: list[Finding] = []
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames or []
    if not header:
        errors.append({"path": str(path), "error": "empty CSV; rules skipped"})
        return findings

    if "perm_read" in header or "perm_unlink" in header:
        findings.append(_finding(_LEGACY_COLUMN_RULE, module, path, 1, ",".join(header)))
        return findings

    for column in ACCESS_CSV_COLUMNS:
        if column not in header:
            findings.append(
                _finding(
                    _MISSING_COLUMN_RULE,
                    module,
                    path,
                    1,
                    f"missing column {column!r}; header is {','.join(header)}",
                )
            )

    if "operation" in header:
        for offset, row in enumerate(reader, start=2):
            operation = (row.get("operation") or "").strip()
            if operation and operation not in VALID_OPERATIONS:
                findings.append(
                    _finding(
                        _BAD_OPERATION_RULE,
                        module,
                        path,
                        offset,
                        f"{row.get('id', '?')}: operation={operation!r}",
                    )
                )
    return findings


# --------------------------------------------------------------------------
# XML
# --------------------------------------------------------------------------


def scan_xml(path: Path, module: str, target: str) -> tuple[list[Finding], list[dict]]:
    """Apply text rules to an XML file, plus the ir.rule removal check."""
    findings: list[Finding] = []
    errors: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for rule in rules_for("xml", target):
        pattern = rule.match.compiled()
        if pattern is None:
            continue
        for offset, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                findings.append(_finding(rule, module, path, offset, line.strip()))

    # ir.rule no longer exists in Odoo 20: record rules are ir.access records
    # with a domain. The XML is searched as text so the check also catches a
    # view that references the model before the module is installable.
    if re.search(r'model=["\']ir\.rule["\']', text):
        for offset, line in enumerate(text.splitlines(), start=1):
            if re.search(r'model=["\']ir\.rule["\']', line):
                findings.append(_finding(_IR_RULE_RULE, module, path, offset, line.strip()))
                break
    return findings, errors


# --------------------------------------------------------------------------
# Python (AST)
# --------------------------------------------------------------------------


class _PythonRuleVisitor(ast.NodeVisitor):
    """Collect raw shapes from a Python file for the registry to match.

    The visitor does not know the rules: it collects calls, keyword argument
    names and function definitions, and matching happens afterwards. That way
    one parse serves every rule.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []  # plain name
        self.attr_calls: list[tuple[str, str, int]] = []  # (receiver, name, lineno)
        self.kwargs: list[tuple[str, int]] = []
        self.definitions: list[tuple[str, int]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name):
            self.calls.append((func.id, node.lineno))
        elif isinstance(func, ast.Attribute):
            receiver = func.value.id if isinstance(func.value, ast.Name) else ""
            self.attr_calls.append((receiver, func.attr, node.lineno))
        for keyword in node.keywords:
            if keyword.arg:
                self.kwargs.append((keyword.arg, node.lineno))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.definitions.append((node.name, node.lineno))
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


def _match_python(
    rule: Rule, visitor: _PythonRuleVisitor, lines: list[str]
) -> list[tuple[int, str]]:
    """Return (line, snippet) for every hit of one rule in a parsed file."""
    match = rule.match
    hits: list[tuple[int, str]] = []

    def snippet(lineno: int) -> str:
        if 1 <= lineno <= len(lines):
            return lines[lineno - 1].strip()
        return ""

    if match.kind == "call":
        for name, lineno in visitor.calls:
            if name == match.name:
                hits.append((lineno, snippet(lineno)))
        # A method call on self/record also matters: `self.check_access_rights()`.
        for _, name, lineno in visitor.attr_calls:
            if name == match.name:
                hits.append((lineno, snippet(lineno)))
    elif match.kind == "call_attr":
        for receiver, name, lineno in visitor.attr_calls:
            if name == match.name and receiver == match.receiver:
                hits.append((lineno, snippet(lineno)))
    elif match.kind == "kwarg":
        for name, lineno in visitor.kwargs:
            if name == match.name:
                hits.append((lineno, snippet(lineno)))
    elif match.kind == "definition":
        for name, lineno in visitor.definitions:
            if name == match.name:
                hits.append((lineno, snippet(lineno)))
    return hits


def scan_python(path: Path, module: str, target: str) -> tuple[list[Finding], list[dict]]:
    """Apply AST and text rules to one Python file."""
    findings: list[Finding] = []
    errors: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        errors.append(
            {
                "path": str(path),
                "error": f"SyntaxError at line {exc.lineno}: {exc.msg}",
            }
        )
        # Text rules still work on an unparseable file, which matters because
        # a file being ported is often mid-edit and temporarily invalid.
        tree = None

    if tree is not None:
        visitor = _PythonRuleVisitor()
        visitor.visit(tree)
        for rule in rules_for("python", target):
            if rule.match.kind == "text":
                continue
            for lineno, snippet_text in _match_python(rule, visitor, lines):
                findings.append(_finding(rule, module, path, lineno, snippet_text))

    for rule in rules_for("python", target):
        if rule.match.kind != "text":
            continue
        pattern = rule.match.compiled()
        if pattern is None:
            continue
        # Comments and docstrings are the documentation a porting developer
        # reads, so a mention there is still worth flagging: it usually means
        # the old API is still in use nearby.
        for offset, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(_finding(rule, module, path, offset, line.strip()))

    return findings, errors


# --------------------------------------------------------------------------
# Module and tree scans
# --------------------------------------------------------------------------


def scan_module(module_dir: Path, target: str = "20.0") -> ModuleScan:
    """Scan one module directory for every rule that applies."""
    module = module_dir.name
    result = ModuleScan(module=module, path=str(module_dir))

    manifest = module_dir / MANIFEST_NAME
    if manifest.is_file():
        findings, errors = scan_manifest(manifest, module, target)
        result.findings.extend(findings)
        result.errors.extend(errors)
        result.files_scanned += 1

    for current, dirnames, filenames in os.walk(module_dir):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        current_path = Path(current)
        for filename in sorted(filenames):
            path = current_path / filename
            suffix = path.suffix.lower()
            if filename in (LEGACY_ACCESS_CSV_NAME, ACCESS_CSV_NAME):
                findings, errors = scan_security(path, module, target)
            elif suffix == ".py":
                findings, errors = scan_python(path, module, target)
            elif suffix == ".xml":
                findings, errors = scan_xml(path, module, target)
            else:
                continue
            result.findings.extend(findings)
            result.errors.extend(errors)
            result.files_scanned += 1

    result.findings.sort(key=lambda finding: (finding.path, finding.line, finding.rule_id))
    return result


def scan_addons(
    roots: Iterable[str | Path],
    target: str = "20.0",
    modules: Optional[Iterable[str]] = None,
) -> AddonsScan:
    """Scan every module under the given addons roots.

    Args:
        roots: directories to search. A root may be a module itself.
        target: Odoo series the rules are evaluated against.
        modules: if given, only these module directory names are scanned.
    """
    root_list = [Path(root).expanduser() for root in roots]
    scan = AddonsScan(target=target, roots=[str(root) for root in root_list])
    wanted = {name for name in modules} if modules else None

    for root in root_list:
        if not root.exists():
            scan.errors.append({"path": str(root), "error": "root does not exist"})
            continue
        if not root.is_dir():
            scan.errors.append({"path": str(root), "error": "root is not a directory"})
            continue
        found, skipped = discover_modules(root)
        scan.skipped.extend(skipped)
        for module_dir in found:
            if wanted is not None and module_dir.name not in wanted:
                continue
            try:
                scan.modules.append(scan_module(module_dir, target))
            except OSError as exc:
                scan.errors.append({"path": str(module_dir), "error": str(exc)})
    return scan


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _finding(rule: Rule, module: str, path: Path, line: int, snippet: str) -> Finding:
    return Finding(
        rule_id=rule.id,
        severity=rule.severity,
        title=rule.title,
        message=rule.message,
        doc=rule.doc,
        module=module,
        path=str(path),
        line=line,
        snippet=snippet,
    )


def _line_of(text: str, needle: str) -> int:
    """First 1-based line containing ``needle``."""
    for offset, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return offset
    return 1


# Structural rules for the security files. These describe the Odoo 20 schema
# rather than a rename, so the scanner enforces them from the file contents;
# the rule text and severity still live in the registry.
_LEGACY_FILE_RULE = get_rule("ODOO20002")
_LEGACY_COLUMN_RULE = get_rule("ODOO20018")
_MISSING_COLUMN_RULE = get_rule("ODOO20016")
_BAD_OPERATION_RULE = get_rule("ODOO20017")
_IR_RULE_RULE = get_rule("ODOO20015")
