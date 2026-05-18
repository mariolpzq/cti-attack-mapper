"""Eval harness: run the extractor on every report in eval/reports/ and compute
per-report and macro-averaged precision/recall/F1 against ground-truth ATT&CK
mappings.

For each pair:
    eval/reports/report_N.txt        - narrative CTI text (no ATT&CK table)
    eval/reports/report_N_truth.json - {"techniques": ["T1059.001", ...]}

Usage:
    uv run python -m eval.run_eval
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from src.agent import extract_techniques

REPORTS_DIR = Path("eval/reports")
RESULTS_PATH = Path("eval/results.md")
PREDICTIONS_DIR = Path("eval/predictions")  # persisted predictions per report


def compute_metrics(predicted: set[str], truth: set[str]) -> dict[str, float]:
    """Strict T-ID exact-match precision / recall / F1."""
    if not predicted and not truth:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    tp = len(predicted & truth)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(truth) if truth else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {"precision": precision, "recall": recall, "f1": f1}


def discover_reports() -> list[tuple[str, Path, Path]]:
    """Find (name, report_path, truth_path) triples in eval/reports/."""
    triples: list[tuple[str, Path, Path]] = []
    for report_path in sorted(REPORTS_DIR.glob("report_*.txt")):
        # report_1.txt -> report_1_truth.json
        stem = report_path.stem
        truth_path = REPORTS_DIR / f"{stem}_truth.json"
        if not truth_path.exists():
            print(f"  (skipping {stem}: no ground truth file)")
            continue
        triples.append((stem, report_path, truth_path))
    return triples


def normalize_tid(tid: str) -> str:
    """Uppercase and strip whitespace so 't1059.001' == 'T1059.001'."""
    return tid.strip().upper()


def load_truth(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {normalize_tid(t) for t in data.get("techniques", [])}


def extract_predicted_tids(result: dict) -> set[str]:
    """Pull T-IDs out of the agent's structured output, validating format."""
    tid_pattern = re.compile(r"^T\d{4}(?:\.\d{3})?$")
    tids: set[str] = set()
    for entry in result.get("techniques", []):
        tid = normalize_tid(entry.get("id", ""))
        if tid_pattern.match(tid):
            tids.add(tid)
    return tids


def main() -> None:
    triples = discover_reports()
    if not triples:
        print(f"No reports found in {REPORTS_DIR}. Add report_N.txt + report_N_truth.json pairs.")
        return

    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    INTER_REPORT_SLEEP = 60  # seconds; avoids hitting Gemini RPM limits across reports

    rows: list[dict] = []
    for i, (name, report_path, truth_path) in enumerate(triples):
        if i > 0:
            print(f"  [rate limit] sleeping {INTER_REPORT_SLEEP}s between reports...", flush=True)
            time.sleep(INTER_REPORT_SLEEP)
        print(f"\n=== {name} ===")
        report_text = report_path.read_text(encoding="utf-8")
        truth = load_truth(truth_path)

        try:
            result = extract_techniques(report_text)
        except Exception as e:
            print(f"  ERROR: {e}")
            rows.append({
                "name": name,
                "predicted": set(),
                "truth": truth,
                "metrics": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
                "error": str(e),
            })
            continue

        # Persist the raw prediction for inspection / error analysis
        (PREDICTIONS_DIR / f"{name}_pred.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        predicted = extract_predicted_tids(result)
        metrics = compute_metrics(predicted, truth)

        print(f"  Predicted: {len(predicted)}  Truth: {len(truth)}")
        print(
            f"  P={metrics['precision']:.2f}  "
            f"R={metrics['recall']:.2f}  "
            f"F1={metrics['f1']:.2f}"
        )
        print(f"  Hits:    {sorted(predicted & truth)}")
        print(f"  Misses:  {sorted(truth - predicted)}")
        print(f"  Extras:  {sorted(predicted - truth)}")

        rows.append({
            "name": name,
            "predicted": predicted,
            "truth": truth,
            "metrics": metrics,
            "error": None,
        })

    write_results(rows)
    print(f"\nResults written to {RESULTS_PATH}")


def write_results(rows: list[dict]) -> None:
    """Emit a markdown table + per-report breakdown to eval/results.md."""
    if not rows:
        return

    macro_p = sum(r["metrics"]["precision"] for r in rows) / len(rows)
    macro_r = sum(r["metrics"]["recall"] for r in rows) / len(rows)
    macro_f1 = sum(r["metrics"]["f1"] for r in rows) / len(rows)

    lines: list[str] = []
    lines.append("# Eval Results\n")
    lines.append("Strict T-ID exact-match precision / recall / F1.\n")
    lines.append("## Summary\n")
    lines.append("| Report | Predicted | Truth | Precision | Recall | F1 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        m = r["metrics"]
        lines.append(
            f"| {r['name']} | {len(r['predicted'])} | {len(r['truth'])} | "
            f"{m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} |"
        )
    lines.append(
        f"| **Macro avg** | | | **{macro_p:.2f}** | **{macro_r:.2f}** | **{macro_f1:.2f}** |"
    )

    lines.append("\n## Per-report details\n")
    for r in rows:
        lines.append(f"### {r['name']}\n")
        if r["error"]:
            lines.append(f"ERROR: {r['error']}\n")
            continue
        lines.append(f"- **Hits** ({len(r['predicted'] & r['truth'])}): "
                     f"{', '.join(sorted(r['predicted'] & r['truth'])) or '—'}")
        lines.append(f"- **Misses** ({len(r['truth'] - r['predicted'])}): "
                     f"{', '.join(sorted(r['truth'] - r['predicted'])) or '—'}")
        lines.append(f"- **Extras** ({len(r['predicted'] - r['truth'])}): "
                     f"{', '.join(sorted(r['predicted'] - r['truth'])) or '—'}")
        lines.append("")

    lines.append("## Error analysis\n")
    lines.append("_TODO after running: pick 2-3 misses and 2-3 false positives, write 2-3 sentences each on why the agent got it wrong._\n")

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
