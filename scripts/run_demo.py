"""Create a placeholder report using only bundled synthetic information."""

from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path("reports") / "synthetic-demo-report.html"


def main() -> int:
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(
        """<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Synthetic Demo Report</title></head>
<body><h1>Offline Operations Data Contract Checker</h1><p>Skeleton synthetic demo report.</p></body></html>
""",
        encoding="utf-8",
    )
    print(f"Created {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
