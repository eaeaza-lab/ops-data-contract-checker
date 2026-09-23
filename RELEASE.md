# Local Release Checklist

Run from the repository root on Windows, offline. Tick each item before tagging a release.

1. [ ] `python -m ops_contract_checker --help` succeeds and shows the `check` command with examples.
2. [ ] `python -m unittest discover -s tests -v` passes.
3. [ ] `python scripts/run_demo.py` writes `reports/synthetic-demo-report.html` (exit code 1 from the checker is expected for the demo data).
4. [ ] `python scripts/verify_demo_report.py` passes.
5. [ ] `python scripts/check.py` passes (runs items 2-4 together).
6. [ ] Every milestone in `PLANS.md` is `[x]` and the Progress log is current.
7. [ ] `SPEC.md` acceptance criteria still match the commands above.
8. [ ] `README.md` describes current behavior, including the demo output.
9. [ ] Fixtures and examples contain synthetic data only: no real company, person, marketplace, or account names, no secrets, no private URLs.
10. [ ] The runtime uses only the Python standard library and makes no network calls.
11. [ ] `git status` shows only intended changes; commit only when explicitly requested.
