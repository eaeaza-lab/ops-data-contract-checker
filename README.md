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

## Project boundaries

This repository uses synthetic data only, runs without network access, and must not contain secrets or real company, person, marketplace, or account names.
