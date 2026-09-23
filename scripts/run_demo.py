"""Run the checker on bundled synthetic files and create the demo HTML report."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ops_contract_checker.cli import EXIT_ERROR, REPORT_FILE, main as cli_main  # noqa: E402

INPUT_PATH = ROOT / "examples" / "data" / "synthetic-orders.csv"
CONTRACT_PATH = ROOT / "examples" / "contracts" / "synthetic-orders.v1.json"
WORK_DIR = ROOT / "reports" / "demo-run"
REPORT_PATH = ROOT / "reports" / "synthetic-demo-report.html"


def main() -> int:
    # Start from a clean directory so the run history is deterministic.
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    code = cli_main(
        [
            "check",
            "--input", str(INPUT_PATH),
            "--contract", str(CONTRACT_PATH),
            "--output", str(WORK_DIR),
        ]
    )
    # The demo data contains deliberate defects, so exit code 1 (findings) is expected.
    if code == EXIT_ERROR:
        return code
    REPORT_PATH.parent.mkdir(exist_ok=True)
    shutil.copyfile(WORK_DIR / REPORT_FILE, REPORT_PATH)
    print(f"Created {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
