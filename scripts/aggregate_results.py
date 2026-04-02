#!/usr/bin/env python3
"""Aggregate batch results and produce a full failure analysis.

Outputs:
- Overall score with difficulty breakdown
- Per-question pass/fail log
- Failure categorization by pattern
"""

import csv
import json
import glob
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_DIR / "results" / "full_eval"
CSV_PATH = PROJECT_DIR / "officeqa_full.csv"
FAILURE_LOG = PROJECT_DIR / "results" / "failure_log.csv"


def main():
    batches = sorted(
        glob.glob(str(RESULTS_DIR / "full246-b*.json")),
        key=lambda f: int(Path(f).stem.split("-b")[1])
    )

    if not batches:
        print("No results found. Run the evaluation first.")
        sys.exit(0)

    # Load question metadata
    qmap = {}
    if CSV_PATH.exists():
        with open(CSV_PATH) as f:
            for r in csv.DictReader(f):
                qmap[f"officeqa-{r['uid'].lower()}"] = r

    # Aggregate all task results
    all_tasks = {}
    total_cost = 0
    total_latency_sum = 0
    total_count = 0

    for bf in batches:
        d = json.load(open(bf))
        total_cost += float(d.get("cost", 0) or 0)
        for task_id, task_data in d.get("tasks", {}).items():
            all_tasks[task_id] = task_data
            total_count += 1
            total_latency_sum += float(task_data.get("latency", 0) or 0)

    passed = [tid for tid, t in all_tasks.items() if t["status"] == "pass"]
    failed = [tid for tid, t in all_tasks.items() if t["status"] == "fail"]

    # Difficulty breakdown
    easy_pass = easy_fail = hard_pass = hard_fail = 0
    for tid in passed:
        q = qmap.get(tid, {})
        if q.get("difficulty") == "easy":
            easy_pass += 1
        else:
            hard_pass += 1
    for tid in failed:
        q = qmap.get(tid, {})
        if q.get("difficulty") == "easy":
            easy_fail += 1
        else:
            hard_fail += 1

    total = len(passed) + len(failed)
    avg_latency = total_latency_sum / total_count if total_count > 0 else 0

    print(f"╔═══════════════════════════════════════════════╗")
    print(f"║  FULL EVALUATION RESULTS                      ║")
    print(f"╠═══════════════════════════════════════════════╣")
    print(f"║  Overall:  {len(passed):3d}/{total} = {len(passed)/total*100:.1f}%{' '*18}║")
    print(f"║  Easy:     {easy_pass:3d}/{easy_pass+easy_fail} = {easy_pass/(easy_pass+easy_fail)*100:.1f}%{' '*18}║" if easy_pass+easy_fail > 0 else "")
    print(f"║  Hard:     {hard_pass:3d}/{hard_pass+hard_fail} = {hard_pass/(hard_pass+hard_fail)*100:.1f}%{' '*18}║" if hard_pass+hard_fail > 0 else "")
    print(f"║  Cost:     ${total_cost:.2f}{' '*(28-len(f'${total_cost:.2f}'))}║")
    print(f"║  Avg lat:  {avg_latency:.0f}s{' '*(30-len(f'{avg_latency:.0f}s'))}║")
    print(f"║  Scored:   {total}/246{' '*(28-len(f'{total}/246'))}║")
    print(f"╚═══════════════════════════════════════════════╝")

    # Write failure log CSV
    with open(FAILURE_LOG, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["uid", "status", "difficulty", "cost", "latency",
                         "expected_answer", "question_preview"])
        for tid in sorted(all_tasks.keys()):
            t = all_tasks[tid]
            q = qmap.get(tid, {})
            writer.writerow([
                tid.replace("officeqa-", ""),
                t["status"],
                q.get("difficulty", ""),
                f"{t.get('cost', 0):.4f}",
                f"{t.get('latency', 0):.0f}",
                q.get("answer", ""),
                q.get("question", "")[:100],
            ])

    print(f"\nPer-question log saved to: {FAILURE_LOG}")

    # Print failed questions summary
    print(f"\n{'='*60}")
    print(f"FAILED QUESTIONS ({len(failed)}):")
    print(f"{'='*60}")
    for tid in sorted(failed):
        q = qmap.get(tid, {})
        diff = q.get("difficulty", "?")
        answer = q.get("answer", "?")
        question = q.get("question", "")[:80]
        print(f"  ✗ {tid.replace('officeqa-',''):8s} [{diff:4s}] GT={answer:>15s}  {question}")

    # Per-batch breakdown
    print(f"\nPer-batch breakdown:")
    for bf in batches:
        d = json.load(open(bf))
        bn = int(d["tag"].split("-b")[1])
        p = int(d.get("passed", 0))
        fl = int(d.get("failed", 0))
        t = p + fl
        pct = p / t * 100 if t else 0
        cost = float(d.get("cost", 0) or 0)
        print(f"  B{bn:2d}: {p:2d}/{t:2d} ({pct:5.1f}%) ${cost:.2f}")


if __name__ == "__main__":
    main()
