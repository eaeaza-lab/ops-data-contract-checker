import unittest
from pathlib import Path

from ops_contract_checker.contract import EXAMPLES_DIR, load_contract
from ops_contract_checker.readers import read_csv_text, read_records
from ops_contract_checker.validation import validate_records

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def findings_for(name):
    contract = load_contract(EXAMPLES_DIR / "synthetic-orders.v1.json")
    result = read_records(FIXTURES / name)
    assert result.ok, [str(p) for p in result.problems]
    return validate_records(result.records, contract, result.columns)


class FixtureTests(unittest.TestCase):
    def test_clean_csv_and_json_fixtures_have_no_findings(self) -> None:
        self.assertEqual(findings_for("clean-orders.csv"), [])
        self.assertEqual(findings_for("clean-orders.json"), [])

    def test_edge_fixture_reports_exactly_the_boundary_defects(self) -> None:
        found = [(f.check, f.row) for f in findings_for("edge-orders.csv")]
        self.assertEqual(
            found,
            [
                ("required", 9),
                ("identifier", 7),
                ("identifier", 8),
                ("duplicate", 10),
                ("total", 5),
                ("date", 3),
                ("date", 4),
                ("currency", 6),
            ],
        )

    def test_edge_fixture_is_deterministic(self) -> None:
        self.assertEqual(findings_for("edge-orders.csv"), findings_for("edge-orders.csv"))


class EdgeCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contract(EXAMPLES_DIR / "synthetic-orders.v1.json")

    def test_header_only_csv_has_no_record_findings(self) -> None:
        result = read_csv_text("record_id,order_date,net_amount,tax_amount,total_amount,currency,note\n")
        self.assertTrue(result.ok)
        self.assertEqual(validate_records(result.records, self.contract, result.columns), [])

    def test_empty_record_list_reports_missing_columns_only(self) -> None:
        findings = validate_records([], self.contract, [])
        self.assertTrue(findings)
        self.assertEqual({f.check for f in findings}, {"schema"})

    def test_blank_lines_and_bom_are_tolerated(self) -> None:
        text = "﻿record_id,order_date,net_amount,tax_amount,total_amount,currency,note\n\nSYN-001,2026-03-01,1,1,2,TST,\n\n"
        result = read_csv_text(text)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.records), 1)


class ReleaseChecklistTests(unittest.TestCase):
    def test_checklist_lists_the_acceptance_commands(self) -> None:
        text = (ROOT / "RELEASE.md").read_text(encoding="utf-8")
        for command in (
            "python -m ops_contract_checker --help",
            "python -m unittest discover -s tests -v",
            "python scripts/run_demo.py",
            "python scripts/verify_demo_report.py",
            "python scripts/check.py",
        ):
            self.assertIn(command, text)


if __name__ == "__main__":
    unittest.main()
