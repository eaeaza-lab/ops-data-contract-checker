"""Self-contained static HTML report for a completed check."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from html import escape

from .validation import CHECKS, Finding

STYLE = """
body { font-family: sans-serif; margin: 2rem; color: #1b1f24; }
h1 { margin-bottom: 0.25rem; }
.meta { color: #57606a; margin-top: 0; }
.status-pass { color: #1a7f37; }
.status-fail { color: #cf222e; }
table { border-collapse: collapse; margin: 1rem 0; }
th, td { border: 1px solid #d0d7de; padding: 0.35rem 0.75rem; text-align: left; }
th { background: #f6f8fa; }
tr:nth-child(even) td { background: #fafbfc; }
code { font-family: monospace; background: #f6f8fa; padding: 0 0.25rem; }
dt { font-weight: bold; margin-top: 0.5rem; }
dd { margin-left: 1.5rem; color: #57606a; }
"""

CHECK_HELP = {
    "schema": "Columns or fields differ from the contract (missing or unexpected).",
    "required": "A required field is blank or absent in a record.",
    "type": "A value does not match the declared field type.",
    "identifier": "An identifier does not match the contract's pattern.",
    "duplicate": "A record repeats the key of an earlier record.",
    "total": "A total does not equal the sum of its components within tolerance.",
    "date": "A date falls outside the contract's allowed range.",
    "currency": "A currency code is not in the contract's allowed list.",
}


def render_report(
    *,
    input_path: str,
    contract_name: str,
    contract_version: str,
    record_count: int,
    findings: Sequence[Finding],
    run_id: int | None = None,
) -> str:
    """Return a complete HTML document; output is deterministic and needs no network."""
    counts = Counter(f.check for f in findings)
    passed = not findings
    status = "PASS" if passed else "FAIL"
    css_class = "status-pass" if passed else "status-fail"
    run_text = "" if run_id is None else f" &middot; run {run_id}"

    summary_rows = "\n".join(
        f"<tr><td>{escape(check)}</td><td>{counts.get(check, 0)}</td></tr>"
        for check in CHECKS
    )
    if findings:
        finding_rows = "\n".join(
            "<tr>"
            f"<td>{escape(f.check)}</td>"
            f"<td>{'file' if f.row is None else f.row}</td>"
            f"<td>{f'<code>{escape(f.field)}</code>' if f.field else ''}</td>"
            f"<td>{escape(f.message)}</td>"
            "</tr>"
            for f in findings
        )
        details = (
            "<table>\n<tr><th>Check</th><th>Record</th><th>Field</th><th>Message</th></tr>\n"
            f"{finding_rows}\n</table>"
        )
    else:
        details = "<p>No findings.</p>"

    legend = "\n".join(
        f"<dt>{escape(check)}</dt><dd>{escape(CHECK_HELP.get(check, ''))}</dd>"
        for check in CHECKS
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Data Contract Report - {escape(contract_name)}</title>
<style>{STYLE}</style></head>
<body>
<h1>Data Contract Report</h1>
<p class="meta">Contract {escape(contract_name)} v{escape(contract_version)}{run_text}<br>
Input: {escape(input_path)}</p>
<h2>Summary</h2>
<p class="{css_class}"><strong>{status}</strong> &mdash; {record_count} record(s) checked, {len(findings)} finding(s).</p>
<table>
<tr><th>Check</th><th>Findings</th></tr>
{summary_rows}
</table>
<h2>Findings</h2>
{details}
<h2>What the checks mean</h2>
<dl>
{legend}
</dl>
</body></html>
"""
