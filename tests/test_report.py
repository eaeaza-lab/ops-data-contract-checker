import unittest

from ops_contract_checker.report import render_report
from ops_contract_checker.validation import Finding


def render(findings):
    return render_report(
        input_path="orders.csv",
        contract_name="synthetic-orders",
        contract_version="1.0.0",
        record_count=3,
        findings=findings,
        run_id=7,
    )


class ReportTests(unittest.TestCase):
    def test_clean_report(self):
        html = render([])
        self.assertIn("PASS", html)
        self.assertIn("No findings.", html)
        self.assertIn("synthetic-orders", html)

    def test_findings_are_listed_and_escaped(self):
        html = render([Finding("total", "bad <b>sum</b>", 2, "total_amount"),
                       Finding("schema", "missing column", None, None)])
        self.assertIn("FAIL", html)
        self.assertIn("bad &lt;b&gt;sum&lt;/b&gt;", html)
        self.assertNotIn("<b>sum</b>", html)
        self.assertIn("<td>file</td>", html)

    def test_is_self_contained_and_deterministic(self):
        html = render([Finding("date", "out of range", 1, "order_date")])
        self.assertEqual(html, render([Finding("date", "out of range", 1, "order_date")]))
        for token in ("http://", "https://", "<script", "<link"):
            self.assertNotIn(token, html)


if __name__ == "__main__":
    unittest.main()
