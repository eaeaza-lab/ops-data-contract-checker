# Execution Plan

## Milestones

- [x] **M0 setup** *(mvp)* — Establish the specification, project rules, offline check runner, and a tested Python package skeleton.  
  Acceptance: `python scripts/check.py`
- [x] **M1 contract model** *(mvp)* — Define and validate the versioned JSON contract format, with bundled synthetic examples.  
  Acceptance: `python -m unittest discover -s tests -v`
- [x] **M2 input readers** *(mvp)* — Read CSV and JSON records deterministically and report input parsing errors.  
  Acceptance: `python -m unittest discover -s tests -v`
- [x] **M3 core validation** *(mvp)* — Implement schema, required-value, identifier, duplicate, total, date, and currency checks.  
  Acceptance: `python -m unittest discover -s tests -v`
- [x] **M4 SQLite run store** *(mvp)* — Persist run metadata and findings locally in SQLite.  
  Acceptance: `python -m unittest discover -s tests -v`
- [ ] **M5 CLI workflow** *(mvp)* — Wire input, contract, output, and SQLite options into a useful offline CLI.  
  Acceptance: `python -m ops_contract_checker --help`
- [ ] **M6 HTML report** *(mvp)* — Generate a self-contained HTML report for a completed check.  
  Acceptance: `python scripts/run_demo.py`
- [ ] **M7 demo and regression checks** *(mvp)* — Complete the synthetic demo and report verification script.  
  Acceptance: `python scripts/verify_demo_report.py`
- [ ] **M8 usability polish** *(polish)* — Improve error messages, report readability, and CLI examples.  
  Acceptance: `python scripts/check.py`
- [ ] **M9 release readiness** *(polish)* — Add deterministic fixtures, edge-case coverage, and a local release checklist.  
  Acceptance: `python scripts/check.py`

## Progress log

- 2026-09-23 — M0 setup completed: initial specification, plan, project operating rules, standard-library Python skeleton, and one passing test.
- 2026-09-24 — M1 contract model completed: `ops_contract_checker/contract.py` (parse/validate/load), two bundled synthetic contracts in `examples/contracts/`, and `tests/test_contract.py`. Could not run interpreters in the sandbox; verified by reading.
- 2026-09-24 — M2 input readers completed: `ops_contract_checker/readers.py` (CSV/JSON readers collecting `InputProblem`s) and `tests/test_readers.py`. Could not run interpreters in the sandbox; verified by reading.
- 2026-09-24 — M3 core validation completed: `validate_records` and `Finding` in `ops_contract_checker/validation.py` (schema, required, type, identifier, duplicate, total, date, currency) with tests in `tests/test_validation.py`. Could not run interpreters in the sandbox; verified by reading.
- 2026-09-24 — M4 SQLite run store completed: `ops_contract_checker/store.py` (`RunStore`, `RunInfo`) and `tests/test_store.py`. Could not run interpreters in the sandbox; verified by reading.

## Decision log

- 2026-09-23 — Use Python 3 standard library for the checker to keep offline setup friction low.
- 2026-09-23 — Use `unittest` rather than a third-party test runner so tests run without package installation.
- 2026-09-23 — Keep report serving optional; generated reports must open directly from disk.
- 2026-09-23 — Keep all examples explicitly synthetic.
- 2026-09-24 — Contracts are strict: unknown keys and undeclared field references are errors, and all problems are collected and reported together rather than failing on the first one.
- 2026-09-24 — Contract `format_version` (currently 1) is separate from the contract's own `version`; example contracts live in `examples/contracts/` and are named `<name>.v1.json`.
- 2026-09-24 — Readers choose the parser by file extension; CSV values stay strings (typing is left to validation); JSON accepts a list of objects or `{"records": [...]}`. Parsing problems are collected in `ReadResult.problems` rather than raised, and bad rows are skipped so later rows still load.
- 2026-09-24 — Total rules use `total_field` + `component_fields` + optional `tolerance` (default 0); date rules use ISO `min`/`max`, either optional.
- 2026-09-24 — Blank values are reported only by the required check; type, identifier, total, date, and currency checks skip blanks, and total checks skip rows with non-numeric parts (already a type finding). A wholly missing column yields one schema finding instead of one required finding per record. Identifier patterns use `re.search` (contracts anchor with `^`/`$`). Duplicate findings point at later occurrences and name the first. Findings are ordered by check, then record position.
- 2026-09-24 — Run store uses two tables (`runs`, `findings`) with an explicit `position` column so findings read back in the order they were saved; the timestamp is injectable (`created_at`) for deterministic tests, and the store never opens the network or writes anything but the given database path.
