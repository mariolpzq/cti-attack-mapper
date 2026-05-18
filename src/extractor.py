"""CLI entry point: extract MITRE ATT&CK techniques from a single CTI report file.

Usage:
    uv run python -m src.extractor path/to/report.txt
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.agent import extract_techniques


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m src.extractor <path/to/report.txt>", file=sys.stderr)
        sys.exit(2)

    report_path = Path(sys.argv[1])
    if not report_path.exists():
        print(f"File not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    report_text = report_path.read_text(encoding="utf-8")
    print(f"Extracting techniques from {report_path} ({len(report_text)} chars)...", file=sys.stderr)

    result = extract_techniques(report_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
