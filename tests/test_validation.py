import unittest

from ops_contract_checker.contract import load_contract
from ops_contract_checker.readers import read_csv_text
from ops_contract_checker.validation import missing_required_fields, validate_records
from ops_contract_checker.contract import EXAMPLES_DIR

HEADER = "record_id,order_date,net_amount,tax_amount,total_amount,currency,note\n"


def checks(findings):
    return [(f.check, f.row) for f in findings]


class MissingRequiredFieldsTests(unittest.TestCase):
    def test_reports_blank_and_absent_fields_in_synthetic_csv_records(self) -> None:
        records = [
            {"record_id": "SYN-100", "currency": "TST"},
            {"record_id": "", "currency": "TST"},
            {"record_id": "SYN-102"},
        ]

        findings = missing_required_fields(records, ["record_id", "currency"])

        self.assertEqual(findings, [(2, "record_id"), (3, "currency")])


class ValidateRecordsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contract(EXAMPLES_DIR / "synthetic-orders.v1.json")

    def run_csv(self, body: str):
        result = read_csv_text(HEADER + body)
        self.assertTrue(result.ok)
        return validate_records(result.records, self.contract, result.columns)

    def test_clean_records_have_no_findings(self) -> None:
        body = (
            "SYN-001,2026-03-01,100.00,10.00,110.00,TST,\n"
            "SYN-002,2026-04-01,50,5,55.005,XTS,ok\n"
        )
        self.assertEqual(self.run_csv(body), [])

    def test_each_check_fires(self) -> None:
        body = (
            "SYN-001,2026-03-01,100,10,110,TST,\n"   # 1 clean
            "SYN-001,2026-03-01,100,10,110,TST,\n"   # 2 duplicate
            "BAD-3,2026-03-01,100,10,110,TST,\n"     # 3 identifier
            "SYN-004,2026-03-01,100,10,150,TST,\n"   # 4 total
            "SYN-005,2027-03-01,100,10,110,TST,\n"   # 5 date
            "SYN-006,2026-03-01,100,10,110,ZZZ,\n"   # 6 currency
            ",2026-03-01,100,10,110,TST,\n"          # 7 required
            "SYN-008,not-a-date,abc,10,110,TST,\n"   # 8 types
        )
        found = checks(self.run_csv(body))
        for expected in [
            ("duplicate", 2),
            ("identifier", 3),
            ("total", 4),
            ("date", 5),
            ("currency", 6),
            ("required", 7),
            ("type", 8),
        ]:
            self.assertIn(expected, found)
        self.assertEqual(sum(1 for c, r in found if r == 8), 2)  # date and number types
        self.assertNotIn(("total", 8), found)  # unparseable values are not also total errors

    def test_schema_drift(self) -> None:
        result = read_csv_text("record_id,order_date,extra\nSYN-001,2026-03-01,x\n")
        findings = validate_records(result.records, self.contract, result.columns)
        messages = [f.message for f in findings if f.check == "schema"]
        self.assertIn("missing column 'currency'", messages)
        self.assertIn("unexpected column 'extra'", messages)
        # missing required columns are not repeated per record
        self.assertFalse([f for f in findings if f.check == "required"])

    def test_json_typed_values_and_derived_columns(self) -> None:
        records = [
            {"record_id": "SYN-001", "order_date": "2026-03-01", "net_amount": 1,
             "tax_amount": 2, "total_amount": 3, "currency": "TST"},
            {"record_id": "SYN-002", "order_date": "2026-03-01", "net_amount": True,
             "tax_amount": 2, "total_amount": 3, "currency": "TST"},
        ]
        findings = validate_records(records, self.contract)
        self.assertEqual(
            [(f.check, f.row) for f in findings if f.check != "schema"], [("type", 2)]
        )

    def test_findings_are_deterministic(self) -> None:
        body = "SYN-1,2027-01-01,1,1,9,ZZZ,\nSYN-1,2027-01-01,1,1,9,ZZZ,\n"
        self.assertEqual(self.run_csv(body), self.run_csv(body))


if __name__ == "__main__":
    unittest.main()
