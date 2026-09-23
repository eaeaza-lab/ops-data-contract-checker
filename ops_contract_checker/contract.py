"""Versioned JSON contract model and validation (standard library only)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

SUPPORTED_FORMAT_VERSION = 1
FIELD_TYPES = ("string", "integer", "number", "date")
EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples" / "contracts"


class ContractError(ValueError):
    """Raised when a contract file is unreadable or invalid."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str = "string"
    required: bool = False


@dataclass(frozen=True)
class IdentifierRule:
    field: str
    pattern: str


@dataclass(frozen=True)
class TotalRule:
    total_field: str
    component_fields: tuple[str, ...]
    tolerance: float = 0.0


@dataclass(frozen=True)
class DateRule:
    field: str
    min: date | None = None
    max: date | None = None


@dataclass(frozen=True)
class CurrencyRule:
    field: str
    allowed: tuple[str, ...]


@dataclass(frozen=True)
class Contract:
    format_version: int
    name: str
    version: str
    fields: tuple[FieldSpec, ...]
    description: str = ""
    identifiers: tuple[IdentifierRule, ...] = ()
    duplicate_keys: tuple[str, ...] = ()
    totals: tuple[TotalRule, ...] = ()
    date_rules: tuple[DateRule, ...] = ()
    currency_rules: tuple[CurrencyRule, ...] = ()

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.fields)

    @property
    def required_fields(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.fields if f.required)


def _parse_date(value: object, where: str, problems: list[str]) -> date | None:
    if not isinstance(value, str):
        problems.append(f"{where} must be an ISO date string (YYYY-MM-DD)")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        problems.append(f"{where} is not a valid ISO date: {value!r}")
        return None


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def parse_contract(data: object) -> Contract:
    """Validate a decoded JSON document and build a Contract, or raise ContractError."""
    problems: list[str] = []
    if not isinstance(data, dict):
        raise ContractError(["contract must be a JSON object"])

    known = {
        "format_version", "name", "version", "description", "fields",
        "identifiers", "duplicate_keys", "totals", "date_rules", "currency_rules",
    }
    for key in sorted(set(data) - known):
        problems.append(f"unknown top-level key: {key!r}")

    format_version = data.get("format_version")
    if format_version != SUPPORTED_FORMAT_VERSION or isinstance(format_version, bool):
        problems.append(f"format_version must be {SUPPORTED_FORMAT_VERSION}")

    for key in ("name", "version"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            problems.append(f"{key} must be a non-empty string")
    description = data.get("description", "")
    if not isinstance(description, str):
        problems.append("description must be a string")
        description = ""

    fields: list[FieldSpec] = []
    raw_fields = data.get("fields")
    if not isinstance(raw_fields, list) or not raw_fields:
        problems.append("fields must be a non-empty list")
        raw_fields = []
    for i, item in enumerate(raw_fields):
        where = f"fields[{i}]"
        if not isinstance(item, dict):
            problems.append(f"{where} must be an object")
            continue
        for key in sorted(set(item) - {"name", "type", "required"}):
            problems.append(f"{where} has unknown key: {key!r}")
        name = item.get("name")
        ftype = item.get("type", "string")
        required = item.get("required", False)
        if not isinstance(name, str) or not name.strip():
            problems.append(f"{where}.name must be a non-empty string")
            continue
        if ftype not in FIELD_TYPES:
            problems.append(f"{where}.type must be one of {', '.join(FIELD_TYPES)}")
            ftype = "string"
        if not isinstance(required, bool):
            problems.append(f"{where}.required must be true or false")
            required = False
        if any(f.name == name for f in fields):
            problems.append(f"{where}.name duplicates field {name!r}")
            continue
        fields.append(FieldSpec(name, ftype, required))
    names = {f.name for f in fields}
    types = {f.name: f.type for f in fields}

    def known_field(value: object, where: str) -> str | None:
        if not isinstance(value, str) or value not in names:
            problems.append(f"{where} must name a declared field")
            return None
        return value

    def rule_list(key: str) -> list[tuple[str, dict]]:
        raw = data.get(key, [])
        if not isinstance(raw, list):
            problems.append(f"{key} must be a list")
            return []
        out = []
        for i, item in enumerate(raw):
            if isinstance(item, dict):
                out.append((f"{key}[{i}]", item))
            else:
                problems.append(f"{key}[{i}] must be an object")
        return out

    identifiers: list[IdentifierRule] = []
    for where, item in rule_list("identifiers"):
        fname = known_field(item.get("field"), f"{where}.field")
        pattern = item.get("pattern")
        try:
            if not isinstance(pattern, str):
                raise TypeError
            re.compile(pattern)
        except TypeError:
            problems.append(f"{where}.pattern must be a string")
            continue
        except re.error as exc:
            problems.append(f"{where}.pattern is not a valid regular expression: {exc}")
            continue
        if fname:
            identifiers.append(IdentifierRule(fname, pattern))

    duplicate_keys: list[str] = []
    raw_keys = data.get("duplicate_keys", [])
    if not isinstance(raw_keys, list):
        problems.append("duplicate_keys must be a list of field names")
    else:
        for i, key in enumerate(raw_keys):
            fname = known_field(key, f"duplicate_keys[{i}]")
            if fname and fname not in duplicate_keys:
                duplicate_keys.append(fname)

    totals: list[TotalRule] = []
    for where, item in rule_list("totals"):
        total = known_field(item.get("total_field"), f"{where}.total_field")
        comps_raw = item.get("component_fields")
        comps: list[str] = []
        if not isinstance(comps_raw, list) or not comps_raw:
            problems.append(f"{where}.component_fields must be a non-empty list")
        else:
            for j, c in enumerate(comps_raw):
                cname = known_field(c, f"{where}.component_fields[{j}]")
                if cname:
                    comps.append(cname)
        tolerance = item.get("tolerance", 0)
        if not _is_number(tolerance) or tolerance < 0:
            problems.append(f"{where}.tolerance must be a non-negative number")
            tolerance = 0
        for fname in ([total] if total else []) + comps:
            if types.get(fname) not in ("integer", "number"):
                problems.append(f"{where} field {fname!r} must be numeric (integer or number)")
        if total and comps:
            totals.append(TotalRule(total, tuple(comps), float(tolerance)))

    date_rules: list[DateRule] = []
    for where, item in rule_list("date_rules"):
        fname = known_field(item.get("field"), f"{where}.field")
        if fname and types.get(fname) != "date":
            problems.append(f"{where}.field {fname!r} must have type 'date'")
        lo = _parse_date(item["min"], f"{where}.min", problems) if "min" in item else None
        hi = _parse_date(item["max"], f"{where}.max", problems) if "max" in item else None
        if "min" not in item and "max" not in item:
            problems.append(f"{where} needs at least one of min or max")
        if lo and hi and lo > hi:
            problems.append(f"{where}.min must not be after max")
        if fname:
            date_rules.append(DateRule(fname, lo, hi))

    currency_rules: list[CurrencyRule] = []
    for where, item in rule_list("currency_rules"):
        fname = known_field(item.get("field"), f"{where}.field")
        allowed = item.get("allowed")
        if (
            not isinstance(allowed, list)
            or not allowed
            or not all(isinstance(a, str) and a for a in allowed)
        ):
            problems.append(f"{where}.allowed must be a non-empty list of strings")
            continue
        if fname:
            currency_rules.append(CurrencyRule(fname, tuple(allowed)))

    if problems:
        raise ContractError(problems)
    return Contract(
        format_version=format_version,
        name=data["name"],
        version=data["version"],
        fields=tuple(fields),
        description=description,
        identifiers=tuple(identifiers),
        duplicate_keys=tuple(duplicate_keys),
        totals=tuple(totals),
        date_rules=tuple(date_rules),
        currency_rules=tuple(currency_rules),
    )


def load_contract(path: str | Path) -> Contract:
    """Read a contract JSON file from disk and validate it."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError([f"cannot read contract {path}: {exc.strerror or exc}"]) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError([f"{path} is not valid JSON: {exc}"]) from exc
    return parse_contract(data)


def bundled_contract_paths() -> list[Path]:
    """Return the bundled synthetic example contracts in a stable order."""
    return sorted(EXAMPLES_DIR.glob("*.json"))
