import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from ops_contract_checker.cli import EXIT_ERROR, EXIT_FINDINGS, EXIT_OK, main
from ops_contract_checker.store import RunStore

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "examples" / "contracts" / "synthetic-orders.v1.json"

HEADER = "record_id,order_date,net_amount,tax_amount,total_amount,currency,note\n"
GOOD = HEADER + "SYN-001,2026-03-01,10.00,2.00,12.00,TST,\n"
BAD = GOOD + "SYN-001,2026-03-02,10.00,2.00,99.00,ZZZ,\n"


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write_input(self, text, name="orders.csv"):
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def check(self, input_path, *extra):
        return run_cli(
            "check", "--input", str(input_path), "--contract", str(CONTRACT),
            "--output", str(self.tmp / "out"), *extra,
        )

    def test_clean_input_exits_zero_and_writes_outputs(self):
        code, out, _ = self.check(self.write_input(GOOD))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("0 finding(s)", out)
        payload = json.loads((self.tmp / "out" / "findings.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["finding_count"], 0)
        self.assertEqual(payload["record_count"], 1)
        report = (self.tmp / "out" / "report.html").read_text(encoding="utf-8")
        self.assertIn("Data Contract Report", report)
        with RunStore(str(self.tmp / "out" / "runs.sqlite")) as store:
            self.assertEqual(len(store.list_runs()), 1)

    def test_findings_exit_one_and_are_stored(self):
        code, out, _ = self.check(self.write_input(BAD), "--db", str(self.tmp / "custom.sqlite"))
        self.assertEqual(code, EXIT_FINDINGS)
        payload = json.loads((self.tmp / "out" / "findings.json").read_text(encoding="utf-8"))
        checks = {f["check"] for f in payload["findings"]}
        self.assertTrue({"duplicate", "total", "currency"} <= checks)
        with RunStore(str(self.tmp / "custom.sqlite")) as store:
            stored = store.get_findings(payload["run_id"])
        self.assertEqual(len(stored), payload["finding_count"])
        self.assertFalse((self.tmp / "out" / "runs.sqlite").exists())

    def test_missing_input_is_error(self):
        code, _, err = self.check(self.tmp / "nope.csv")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("not found", err)

    def test_invalid_contract_is_error(self):
        bad = self.tmp / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        code, _, err = run_cli(
            "check", "--input", str(self.write_input(GOOD)), "--contract", str(bad),
            "--output", str(self.tmp / "out"),
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("invalid contract", err)

    def test_no_command_prints_help(self):
        code, out, _ = run_cli()
        self.assertEqual(code, EXIT_OK)
        self.assertIn("check", out)


if __name__ == "__main__":
    unittest.main()
