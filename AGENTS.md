# Future Session Guide

## Commands

- Run all checks: `python scripts/check.py`
- Run tests: `python -m unittest discover -s tests -v`
- Inspect CLI: `python -m ops_contract_checker --help`

## Rules

- Keep the application offline at runtime and use Python standard library unless a dependency is explicitly approved.
- Use synthetic fixtures only. Do not add real company, person, marketplace, or account names.
- Do not add secrets, credentials, tokens, or private URLs.
- Preserve versioned contracts as JSON and keep their behavior covered by tests.
- Generate reports that work when opened from disk; Node's built-in HTTP server may be documented for optional local viewing, but is not required by the checker.
- Update `SPEC.md`, `PLANS.md`, and tests when MVP behavior changes.
- Keep `.nightshift.json` commands Windows-compatible, offline, and within its allowed command prefixes. Put multi-step checks in a Python script.
- Do not commit unless explicitly asked.
