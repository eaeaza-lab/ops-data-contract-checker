"""Small, dependency-free validation primitives for the first milestone."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def missing_required_fields(
    records: Iterable[Mapping[str, object]], required_fields: Iterable[str]
) -> list[tuple[int, str]]:
    """Return one-based record positions and required fields that are blank or absent."""
    findings: list[tuple[int, str]] = []
    required = tuple(required_fields)
    for position, record in enumerate(records, start=1):
        for field in required:
            value = record.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                findings.append((position, field))
    return findings
