import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify_demo_report  # noqa: E402

from ops_contract_checker.contract import load_contract  # noqa: E402
from ops_contract_checker.readers import read_records  # noqa: E402
from ops_contract_checker.report import render_report  # noqa: E402
from ops_contract_checker.validation import CHECKS, validate_records  # noqa: E402


def demo_findings():
    contract = load_contract(str(ROOT / "examples" / "contracts" / "synthetic-orders.v1.json"))
    result = read_records(str(ROOT / "examples" / "data" / "synthetic-orders.csv"))
    return contract, result, validate_records(result.records, contract, result.columns)


class DemoVerifyTests(unittest.TestCase):
    def test_demo_data_matches_expected_counts(self):
        _, result, findings = demo_findings()
        counts = Counter(f.check for f in findings)
        self.assertEqual(len(result.records), verify_demo_report.EXPECTED_RECORDS)
        self.assertEqual(
            {check: counts.get(check, 0) for check in CHECKS},
            verify_demo_report.EXPECTED_COUNTS,
        )

    def test_verify_accepts_real_report_and_rejects_others(self):
        contract, result, findings = demo_findings()
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.html"
            good.write_text(
                render_report(
                    input_path="synthetic-orders.csv",
                    contract_name=contract.name,
                    contract_version=contract.version,
                    record_count=len(result.records),
                    findings=findings,
                ),
                encoding="utf-8",
            )
            self.assertEqual(verify_demo_report.verify(good, Path(tmp) / "none.json"), [])

            bad = Path(tmp) / "bad.html"
            bad.write_text(
                render_report(
                    input_path="synthetic-orders.csv",
                    contract_name=contract.name,
                    contract_version=contract.version,
                    record_count=len(result.records),
                    findings=[],
                ),
                encoding="utf-8",
            )
            self.assertTrue(verify_demo_report.verify(bad, Path(tmp) / "none.json"))

    def test_missing_report_is_reported(self):
        problems = verify_demo_report.verify(Path("does-not-exist.html"))
        self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
