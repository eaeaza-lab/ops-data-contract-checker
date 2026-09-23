"""Offline command-line workflow: read input, validate, store the run, write findings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .contract import ContractError, load_contract
from .readers import read_records
from .report import render_report
from .store import RunStore
from .validation import validate_records

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

FINDINGS_FILE = "findings.json"
REPORT_FILE = "report.html"
DEFAULT_DB_NAME = "runs.sqlite"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops-contract-checker",
        description="Validate synthetic CSV and JSON exports against versioned data contracts.",
        epilog="exit codes: 0 no findings, 1 findings reported, 2 usage or input error",
    )
    parser.add_argument(
        "--version", action="version", version=f"ops-contract-checker {__version__}"
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    check = sub.add_parser(
        "check",
        help="check a CSV or JSON export against a contract",
        description="Check a CSV or JSON export against a versioned JSON contract, "
        f"store the run in SQLite, and write {REPORT_FILE} and {FINDINGS_FILE} to the output directory.",
    )
    check.add_argument("--input", required=True, help="path to the .csv or .json export")
    check.add_argument("--contract", required=True, help="path to the JSON contract")
    check.add_argument("--output", required=True, help="output directory (created if missing)")
    check.add_argument(
        "--db",
        help=f"SQLite file for run history (default: <output>/{DEFAULT_DB_NAME})",
    )
    return parser


def run_check(args: argparse.Namespace) -> int:
    try:
        contract = load_contract(args.contract)
    except ContractError as exc:
        print(f"error: invalid contract {args.contract}:\n{exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(f"error: cannot read contract: {exc}", file=sys.stderr)
        return EXIT_ERROR

    result = read_records(args.input)
    if result.problems:
        print(f"error: cannot read input {args.input}:", file=sys.stderr)
        for problem in result.problems:
            print(f"  {problem}", file=sys.stderr)
        return EXIT_ERROR

    findings = validate_records(result.records, contract, result.columns)

    output = Path(args.output)
    db_path = Path(args.db) if args.db else output / DEFAULT_DB_NAME
    try:
        output.mkdir(parents=True, exist_ok=True)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with RunStore(str(db_path)) as store:
            run_id = store.save_run(
                args.input,
                contract.name,
                contract.version,
                len(result.records),
                findings,
            )
        payload = {
            "run_id": run_id,
            "input": str(args.input),
            "contract": {"name": contract.name, "version": contract.version},
            "record_count": len(result.records),
            "finding_count": len(findings),
            "findings": [
                {"check": f.check, "message": f.message, "row": f.row, "field": f.field}
                for f in findings
            ],
        }
        (output / FINDINGS_FILE).write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        (output / REPORT_FILE).write_text(
            render_report(
                input_path=str(args.input),
                contract_name=contract.name,
                contract_version=contract.version,
                record_count=len(result.records),
                findings=findings,
                run_id=run_id,
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"error: cannot write output: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(
        f"Checked {len(result.records)} records against {contract.name} v{contract.version}: "
        f"{len(findings)} finding(s)."
    )
    for finding in findings:
        print(f"  {finding}")
    print(f"Run {run_id} stored in {db_path}; findings written to {output / FINDINGS_FILE}")
    print(f"HTML report written to {output / REPORT_FILE}")
    return EXIT_FINDINGS if findings else EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return run_check(args)
    parser.print_help()
    return EXIT_OK
