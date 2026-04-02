#!/usr/bin/env python3
"""Compare two iteration result files and detect regressions.

Usage:
    python3 scripts/compare_runs.py results_old.csv results_new.csv

Input CSV format (one row per question):
    uid,predicted,correct
    q001,543.21,1
    q002,1200,0
    ...

Output:
    - Regressions: questions that went correct -> wrong
    - Fixes: questions that went wrong -> correct
    - Net change: +/- N questions
    - Per-category breakdown if officeqa_full.csv is available
"""

import sys
import csv
import os
from collections import defaultdict


def load_results(filepath):
    """Load a results CSV into {uid: correct} dict."""
    results = {}
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row["uid"]
            correct = int(row["correct"]) if row.get("correct") else 0
            results[uid] = {
                "correct": correct,
                "predicted": row.get("predicted", ""),
            }
    return results


def load_ground_truth(officeqa_path):
    """Load question metadata from officeqa_full.csv if available."""
    if not os.path.exists(officeqa_path):
        return {}
    meta = {}
    with open(officeqa_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            meta[row["uid"]] = {
                "question": row.get("question", "")[:100],
                "answer": row.get("answer", ""),
                "difficulty": row.get("difficulty", ""),
                "source_files": row.get("source_files", ""),
            }
    return meta


def compare(old_path, new_path, officeqa_path=None):
    old = load_results(old_path)
    new = load_results(new_path)

    if not officeqa_path:
        # Try common locations
        for candidate in [
            "officeqa_full.csv",
            "../officeqa/officeqa_full.csv",
            os.path.expanduser("~/officeqa/officeqa_full.csv"),
        ]:
            if os.path.exists(candidate):
                officeqa_path = candidate
                break

    meta = load_ground_truth(officeqa_path) if officeqa_path else {}

    all_uids = set(old.keys()) | set(new.keys())

    regressions = []
    fixes = []
    unchanged_correct = 0
    unchanged_wrong = 0

    for uid in sorted(all_uids):
        old_correct = old.get(uid, {}).get("correct", 0)
        new_correct = new.get(uid, {}).get("correct", 0)

        if old_correct == 1 and new_correct == 0:
            regressions.append(uid)
        elif old_correct == 0 and new_correct == 1:
            fixes.append(uid)
        elif old_correct == 1 and new_correct == 1:
            unchanged_correct += 1
        else:
            unchanged_wrong += 1

    # Print results
    old_score = sum(1 for v in old.values() if v["correct"])
    new_score = sum(1 for v in new.values() if v["correct"])

    print(f"OLD: {old_score}/{len(old)} ({100*old_score/len(old):.1f}%)")
    print(f"NEW: {new_score}/{len(new)} ({100*new_score/len(new):.1f}%)")
    print(f"NET: {'+' if new_score >= old_score else ''}{new_score - old_score}")
    print()

    if regressions:
        print(f"REGRESSIONS ({len(regressions)} questions went correct -> wrong):")
        for uid in regressions:
            m = meta.get(uid, {})
            difficulty = f" [{m['difficulty']}]" if m.get("difficulty") else ""
            question = f" {m['question']}..." if m.get("question") else ""
            old_pred = old.get(uid, {}).get("predicted", "?")
            new_pred = new.get(uid, {}).get("predicted", "?")
            print(f"  {uid}{difficulty}: {old_pred} -> {new_pred}{question}")
        print()

    if fixes:
        print(f"FIXES ({len(fixes)} questions went wrong -> correct):")
        for uid in fixes:
            m = meta.get(uid, {})
            difficulty = f" [{m['difficulty']}]" if m.get("difficulty") else ""
            question = f" {m['question']}..." if m.get("question") else ""
            print(f"  {uid}{difficulty}{question}")
        print()

    print(f"Unchanged correct: {unchanged_correct}")
    print(f"Unchanged wrong:   {unchanged_wrong}")

    # Difficulty breakdown
    if meta:
        print("\nBy difficulty:")
        for diff in ["easy", "hard"]:
            diff_uids = [u for u in all_uids if meta.get(u, {}).get("difficulty") == diff]
            reg_count = len([u for u in regressions if u in diff_uids])
            fix_count = len([u for u in fixes if u in diff_uids])
            print(f"  {diff}: +{fix_count} fixes, -{reg_count} regressions")

    return len(regressions) == 0  # True if no regressions


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/compare_runs.py old_results.csv new_results.csv [officeqa_full.csv]")
        sys.exit(1)

    oqa = sys.argv[3] if len(sys.argv) > 3 else None
    success = compare(sys.argv[1], sys.argv[2], oqa)
    sys.exit(0 if success else 1)
