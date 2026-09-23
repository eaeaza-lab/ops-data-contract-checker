# Offline Operations Data Contract Checker

Status: **work in progress**

A local, offline CLI for checking synthetic CSV and JSON exports against versioned business data contracts. It is intended to flag schema drift, duplicate records, invalid identifiers, broken totals, and suspicious date or currency changes, then produce a clear HTML quality report.

Built by a supervised autonomous agent pipeline (nightshift).

## Requirements

- Python 3.11 or later (standard library only)

## Run

From the repository root:

```text
python -m ops_contract_checker --help
python -m unittest discover -s tests -v
python scripts/check.py
```

`python scripts/check.py` also produces the synthetic demo report at `reports/synthetic-demo-report.html`. Remaining milestones are tracked in [PLANS.md](PLANS.md).

## Contracts

Contracts are versioned JSON files (`format_version: 1`) declaring fields (with type and required flag), identifier patterns, duplicate keys, total rules, date ranges, and allowed currencies. Load and validate them with `ops_contract_checker.contract.load_contract`; invalid contracts raise `ContractError` listing every problem. Synthetic examples are in `examples/contracts/`.

## Input readers

`ops_contract_checker.readers.read_records(path)` reads a `.csv` or `.json` file (UTF-8) and returns a `ReadResult` with `records`, `columns`, and `problems`. CSV values stay strings; JSON may be a list of objects or `{"records": [...]}`. Parsing errors (empty input, bad header, wrong column count, invalid JSON, non-object records, missing file) are collected as `InputProblem`s instead of raised.

## Validation

`ops_contract_checker.validation.validate_records(records, contract, columns)` returns a deterministic list of `Finding`s (`check`, `message`, `row`, `field`). Checks: `schema` (missing/unexpected columns), `required`, `type`, `identifier`, `duplicate`, `total`, `date`, and `currency`. Blank values are reported only as `required`.

## Run store

`ops_contract_checker.store.RunStore(path)` keeps check runs in a local SQLite file (or `:memory:`). `save_run(input_path, contract_name, contract_version, record_count, findings)` returns a run id; `get_run`, `list_runs`, and `get_findings` read it back, with findings in their saved order.

## CLI

```text
python -m ops_contract_checker check --input orders.csv --contract examples/contracts/synthetic-orders.v1.json --output out
```

Reads the input, validates it, stores the run in `out/runs.sqlite` (override with `--db`), writes `out/report.html` and `out/findings.json`, and prints the findings. Exit codes: `0` no findings, `1` findings reported, `2` unreadable contract, input, or output.

## HTML report

`ops_contract_checker.report.render_report(...)` builds a single self-contained HTML page (inline CSS, no scripts or network references, deterministic output) with a pass/fail summary, per-check counts, and a table of findings. Open `report.html` directly from disk. `python scripts/run_demo.py` checks `examples/data/synthetic-orders.csv` (which has deliberate defects) and copies the report to `reports/synthetic-demo-report.html`.

## Project boundaries

This repository uses synthetic data only, runs without network access, and must not contain secrets or real company, person, marketplace, or account names.
