"""Deterministic CSV and JSON record readers (standard library only)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class InputProblem:
    """One input parsing problem; `row` is a one-based record position or None."""

    message: str
    row: int | None = None

    def __str__(self) -> str:
        return self.message if self.row is None else f"record {self.row}: {self.message}"


@dataclass
class ReadResult:
    records: list[dict[str, object]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    problems: list[InputProblem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def read_csv_text(text: str) -> ReadResult:
    """Parse CSV text. Values stay strings; record order follows the file."""
    result = ReadResult()
    if text.startswith("﻿"):
        text = text[1:]
    if not text.strip():
        result.problems.append(InputProblem("CSV input is empty"))
        return result
    reader = csv.reader(text.splitlines())
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:
        result.problems.append(InputProblem(f"cannot read CSV header: {exc}"))
        return result
    header = [name.strip() for name in header]
    seen: set[str] = set()
    for name in header:
        if not name:
            result.problems.append(InputProblem("CSV header contains an empty column name"))
        elif name in seen:
            result.problems.append(InputProblem(f"CSV header repeats column '{name}'"))
        seen.add(name)
    result.columns = header
    position = 0
    while True:
        try:
            row = next(reader)
        except StopIteration:
            break
        except csv.Error as exc:
            result.problems.append(InputProblem(f"malformed CSV: {exc}"))
            break
        if not row:
            continue  # skip blank lines
        position += 1
        if len(row) != len(header):
            result.problems.append(
                InputProblem(f"expected {len(header)} values but found {len(row)}", position)
            )
            continue
        result.records.append(dict(zip(header, row)))
    return result


def read_json_text(text: str) -> ReadResult:
    """Parse JSON text: a list of objects, or an object with a `records` list."""
    result = ReadResult()
    if text.startswith("﻿"):
        text = text[1:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        result.problems.append(
            InputProblem(f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}")
        )
        return result
    if isinstance(data, dict) and "records" in data:
        data = data["records"]
    if not isinstance(data, list):
        result.problems.append(
            InputProblem("JSON input must be a list of objects or an object with a 'records' list")
        )
        return result
    columns: list[str] = []
    for position, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            result.problems.append(InputProblem("record is not a JSON object", position))
            continue
        for key in item:
            if key not in columns:
                columns.append(key)
        result.records.append(dict(item))
    result.columns = columns
    return result


def read_records(path: str | Path) -> ReadResult:
    """Read a `.csv` or `.json` file, choosing the parser by extension."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".csv", ".json"):
        return ReadResult(problems=[InputProblem(f"unsupported input type '{suffix}' (use .csv or .json)")])
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ReadResult(problems=[InputProblem(f"input file not found: {path}")])
    except UnicodeDecodeError:
        return ReadResult(problems=[InputProblem("input file is not valid UTF-8")])
    except OSError as exc:
        return ReadResult(problems=[InputProblem(f"cannot read input file: {exc}")])
    return read_csv_text(text) if suffix == ".csv" else read_json_text(text)
