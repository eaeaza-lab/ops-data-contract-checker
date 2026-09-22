# Offline Operations Data Contract Checker — Specification

## Problem

Operations teams receive CSV and JSON exports that can silently change shape or contain bad records. Discovering missing columns, repeated records, malformed identifiers, broken totals, or unexpected date and currency values after an import is slow and risky. This project provides a local command-line checker that compares a synthetic export with a versioned contract and produces a readable HTML quality report.

## Target user

An operations analyst, data engineer, or implementation specialist who needs a repeatable, offline pre-import quality check for synthetic data exports.

## MVP scope

- A Python 3 CLI that accepts a CSV or JSON input, a versioned JSON contract, and an output directory.
- Contract fields for schema, required fields, identifier rules, duplicate keys, numeric totals, date ranges, and allowed currencies.
- Checks for schema drift, missing required values, duplicate records, invalid identifiers, broken record totals, suspicious dates, and unsupported currencies.
- SQLite-backed storage of a check run and its findings.
- A self-contained static HTML report with summary counts and per-finding details.
- Synthetic example data and contracts only; no network calls at runtime.

## Explicit non-goals

- Connecting to production databases, cloud services, APIs, spreadsheets, or marketplaces.
- Processing personally identifying, account, or real-company data.
- Correcting source data automatically.
- A web server, authentication, multi-user workflow, or hosted SaaS deployment.
- A general-purpose ETL system or support for formats beyond CSV and JSON in the MVP.

## Acceptance criteria

Each criterion is independently checkable from the repository root on Windows while offline.

1. The CLI help command succeeds and describes the checker command.
   - Command: `python -m ops_contract_checker --help`
2. The test suite succeeds, including a synthetic CSV validation test.
   - Command: `python -m unittest discover -s tests -v`
3. The demo check creates an HTML report from only bundled synthetic files.
   - Command: `python scripts/run_demo.py`
4. The demo report exists at the documented location after the demo command runs.
   - Command: `python scripts/verify_demo_report.py`
5. All configured offline checks succeed.
   - Command: `python scripts/check.py`
