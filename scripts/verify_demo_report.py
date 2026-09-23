"""Verify that the synthetic demo report was generated and shows the expected defects."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "reports" / "synthetic-demo-report.html"
FINDINGS_PATH = ROOT / "reports" / "demo-run" / "findings.json"

# The bundled demo data has exactly one deliberate defect per check below.
EXPECTED_COUNTS = {
    "schema": 0,
    "required": 1,
    "type": 0,
    "identifier": 1,
    "duplicate": 1,
    "total": 1,
    "date": 1,
    "currency": 1,
}
EXPECTED_RECORDS = 8

ROW_PATTERN = re.compile(r"<tr><td>([a-z]+)</td><td>(\d+)</td></tr>")


def verify(report_path: Path = REPORT_PATH, findings_path: Path = FINDINGS_PATH) -> list[str]:
    """Return a list of problems; an empty list means the demo report is correct."""
    if not report_path.is_file():
        return [f"Missing demo report: {report_path}"]
    text = report_path.read_text(encoding="utf-8")
    problems: list[str] = []

    for needle in ("Data Contract Report", "synthetic-orders", "<strong>FAIL</strong>"):
        if needle not in text:
            problems.append(f"Report lacks {needle!r}")
    if f"{EXPECTED_RECORDS} record(s) checked" not in text:
        problems.append(f"Report does not show {EXPECTED_RECORDS} records checked")
    if "<script" in text or "http://" in text or "https://" in text:
        problems.append("Report is not self-contained (script or URL found)")

    counts = {check: int(n) for check, n in ROW_PATTERN.findall(text)}
    for check, expected in EXPECTED_COUNTS.items():
        actual = counts.get(check)
        if actual != expected:
            problems.append(f"Check {check!r}: expected {expected} finding(s), report shows {actual}")

    if findings_path.is_file():
        payload = json.loads(findings_path.read_text(encoding="utf-8"))
        if payload.get("finding_count") != sum(EXPECTED_COUNTS.values()):
            problems.append(
                f"findings.json has {payload.get('finding_count')} finding(s), "
                f"expected {sum(EXPECTED_COUNTS.values())}"
            )
    return problems


def main() -> int:
    problems = verify()
    if problems:
        for problem in problems:
            print(problem)
        return 1
    print(f"Verified {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
