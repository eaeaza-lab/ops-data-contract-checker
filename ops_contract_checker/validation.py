"""Dependency-free validation of records against a contract."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from .contract import Contract

CHECKS = (
    "schema",
    "required",
    "type",
    "identifier",
    "duplicate",
    "total",
    "date",
    "currency",
)


@dataclass(frozen=True)
class Finding:
    """One validation finding; `row` is a one-based record position or None for file-level."""

    check: str
    message: str
    row: int | None = None
    field: str | None = None

    def __str__(self) -> str:
        where = "" if self.row is None else f"record {self.row}: "
        return f"[{self.check}] {where}{self.message}"


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _to_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    return number if math.isfinite(number) else None


def _to_integer(value: object) -> int | None:
    number = _to_number(value)
    if number is None or number != int(number):
        return None
    if isinstance(value, str) and not re.fullmatch(r"[+-]?\d+", value.strip()):
        return None
    return int(number)


def _to_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def missing_required_fields(
    records: Iterable[Mapping[str, object]], required_fields: Iterable[str]
) -> list[tuple[int, str]]:
    """Return one-based record positions and required fields that are blank or absent."""
    findings: list[tuple[int, str]] = []
    required = tuple(required_fields)
    for position, record in enumerate(records, start=1):
        for field in required:
            if _is_blank(record.get(field)):
                findings.append((position, field))
    return findings


def validate_records(
    records: Sequence[Mapping[str, object]],
    contract: Contract,
    columns: Sequence[str] | None = None,
) -> list[Finding]:
    """Check records against a contract; findings come in a deterministic order.

    `columns` is the observed column list (from a reader). When omitted it is
    derived from the records in first-seen order. Blank values are reported only
    by the required check, so other checks skip them.
    """
    if columns is None:
        seen: list[str] = []
        for record in records:
            for key in record:
                if key not in seen:
                    seen.append(key)
        columns = seen
    findings: list[Finding] = []
    declared = contract.field_names
    types = {f.name: f.type for f in contract.fields}

    # Schema drift: declared columns that vanished and columns the contract does not know.
    for name in declared:
        if name not in columns:
            findings.append(Finding("schema", f"missing column '{name}'", None, name))
    for name in columns:
        if name not in declared:
            findings.append(Finding("schema", f"unexpected column '{name}'", None, name))
    missing_columns = {name for name in declared if name not in columns}

    # Required values (a wholly missing column is already a schema finding).
    for position, name in missing_required_fields(
        records, [n for n in contract.required_fields if n not in missing_columns]
    ):
        findings.append(Finding("required", f"required field '{name}' is blank", position, name))

    # Types.
    checkers = {"integer": _to_integer, "number": _to_number, "date": _to_date}
    for position, record in enumerate(records, start=1):
        for name in declared:
            value = record.get(name)
            parse = checkers.get(types[name])
            if parse is None or _is_blank(value):
                continue
            if parse(value) is None:
                findings.append(
                    Finding("type", f"'{name}' is not a valid {types[name]}: {value!r}", position, name)
                )

    for rule in contract.identifiers:
        pattern = re.compile(rule.pattern)
        for position, record in enumerate(records, start=1):
            value = record.get(rule.field)
            if _is_blank(value):
                continue
            if not isinstance(value, str) or not pattern.search(value):
                findings.append(
                    Finding(
                        "identifier",
                        f"'{rule.field}' value {value!r} does not match pattern {rule.pattern}",
                        position,
                        rule.field,
                    )
                )

    if contract.duplicate_keys:
        first_seen: dict[tuple[str, ...], int] = {}
        label = ", ".join(contract.duplicate_keys)
        for position, record in enumerate(records, start=1):
            values = [record.get(k) for k in contract.duplicate_keys]
            if any(_is_blank(v) for v in values):
                continue
            key = tuple(str(v).strip() for v in values)
            if key in first_seen:
                findings.append(
                    Finding(
                        "duplicate",
                        f"duplicate key ({label}) = ({', '.join(key)}); first seen at record {first_seen[key]}",
                        position,
                        contract.duplicate_keys[0],
                    )
                )
            else:
                first_seen[key] = position

    for rule in contract.totals:
        for position, record in enumerate(records, start=1):
            total = _to_number(record.get(rule.total_field))
            parts = [_to_number(record.get(c)) for c in rule.component_fields]
            if total is None or any(p is None for p in parts):
                continue  # blank or non-numeric values are reported by other checks
            expected = sum(parts)  # type: ignore[arg-type]
            if abs(total - expected) > rule.tolerance + 1e-9:
                findings.append(
                    Finding(
                        "total",
                        f"'{rule.total_field}' is {total:g} but "
                        f"{' + '.join(rule.component_fields)} is {expected:g}",
                        position,
                        rule.total_field,
                    )
                )

    for rule in contract.date_rules:
        for position, record in enumerate(records, start=1):
            value = record.get(rule.field)
            parsed = _to_date(value)
            if parsed is None:
                continue
            if (rule.min and parsed < rule.min) or (rule.max and parsed > rule.max):
                bounds = f"{rule.min or '...'} to {rule.max or '...'}"
                findings.append(
                    Finding(
                        "date",
                        f"'{rule.field}' {parsed.isoformat()} is outside {bounds}",
                        position,
                        rule.field,
                    )
                )

    for rule in contract.currency_rules:
        for position, record in enumerate(records, start=1):
            value = record.get(rule.field)
            if _is_blank(value):
                continue
            if not isinstance(value, str) or value.strip() not in rule.allowed:
                findings.append(
                    Finding(
                        "currency",
                        f"'{rule.field}' value {value!r} is not one of {', '.join(rule.allowed)}",
                        position,
                        rule.field,
                    )
                )

    return findings
