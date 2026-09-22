import unittest

from ops_contract_checker.validation import missing_required_fields


class MissingRequiredFieldsTests(unittest.TestCase):
    def test_reports_blank_and_absent_fields_in_synthetic_csv_records(self) -> None:
        records = [
            {"record_id": "SYN-100", "currency": "TST"},
            {"record_id": "", "currency": "TST"},
            {"record_id": "SYN-102"},
        ]

        findings = missing_required_fields(records, ["record_id", "currency"])

        self.assertEqual(findings, [(2, "record_id"), (3, "currency")])
