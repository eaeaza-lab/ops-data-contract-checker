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

`python scripts/check.py` also produces the current synthetic placeholder report at `reports/synthetic-demo-report.html`. The validation workflow and sample data will be added during the MVP milestones in [PLANS.md](PLANS.md).

## Contracts

Contracts are versioned JSON files (`format_version: 1`) declaring fields (with type and required flag), identifier patterns, duplicate keys, total rules, date ranges, and allowed currencies. Load and validate them with `ops_contract_checker.contract.load_contract`; invalid contracts raise `ContractError` listing every problem. Synthetic examples are in `examples/contracts/`.

## Input readers

`ops_contract_checker.readers.read_records(path)` reads a `.csv` or `.json` file (UTF-8) and returns a `ReadResult` with `records`, `columns`, and `problems`. CSV values stay strings; JSON may be a list of objects or `{"records": [...]}`. Parsing errors (empty input, bad header, wrong column count, invalid JSON, non-object records, missing file) are collected as `InputProblem`s instead of raised.

## Project boundaries

This repository uses synthetic data only, runs without network access, and must not contain secrets or real company, person, marketplace, or account names.
