"""Verify that the synthetic demo report was generated."""

from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path("reports") / "synthetic-demo-report.html"


def main() -> int:
    if not REPORT_PATH.is_file():
        print(f"Missing demo report: {REPORT_PATH}")
        return 1
    text = REPORT_PATH.read_text(encoding="utf-8")
    if "Data Contract Report" not in text or "synthetic-orders" not in text:
        print(f"Unexpected demo report contents: {REPORT_PATH}")
        return 1
    print(f"Verified {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
