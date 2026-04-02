#!/usr/bin/env python3
"""Score a results file locally using 1% fuzzy numeric tolerance.

Usage:
    python3 scripts/local_score.py results.csv [officeqa_full.csv]

Input CSV format:
    uid,predicted
    q001,543.21
    q002,1200
    ...

Loads ground truth from officeqa_full.csv and scores each prediction.
Outputs per-question results and aggregate score.
"""

import sys
import csv
import os
import re


def parse_number(s):
    """Extract a numeric value from a string answer."""
    if s is None or str(s).strip() == "":
        return None
    s = str(s).strip()
    # Remove common non-numeric artifacts
    s = s.replace(",", "").replace("$", "").replace("%", "")
    # Handle parenthetical negatives: (123) -> -123
    paren_match = re.match(r"^\(([0-9.]+)\)$", s)
    if paren_match:
        s = "-" + paren_match.group(1)
    try:
        return float(s)
    except ValueError:
        return None


def score_answer(predicted, truth, tolerance=0.01):
    """Score a single answer. Returns (correct, error_pct)."""
    pred_num = parse_number(predicted)
    truth_num = parse_number(truth)

    if pred_num is None or truth_num is None:
        return False, None

    if truth_num == 0:
        # Exact match required for zero
        return pred_num == 0, abs(pred_num) * 100 if pred_num != 0 else 0

    error = abs(pred_num - truth_num) / abs(truth_num)
    return error <= tolerance, error * 100


def main(results_path, officeqa_path=None):
    # Find officeqa_full.csv
    if not officeqa_path:
        for candidate in [
            "officeqa_full.csv",
            "../officeqa/officeqa_full.csv",
            os.path.expanduser("~/officeqa/officeqa_full.csv"),
        ]:
            if os.path.exists(candidate):
                officeqa_path = candidate
                break

    if not officeqa_path or not os.path.exists(officeqa_path):
        print("ERROR: Cannot find officeqa_full.csv. Provide path as second argument.")
        sys.exit(1)

    # Load ground truth
    truth = {}
    meta = {}
    with open(officeqa_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            truth[row["uid"]] = row["answer"]
            meta[row["uid"]] = {
                "difficulty": row.get("difficulty", ""),
                "question": row.get("question", "")[:80],
            }

    # Load predictions
    predictions = {}
    with open(results_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            predictions[row["uid"]] = row["predicted"]

    # Score
    results = []
    correct_total = 0
    correct_easy = 0
    correct_hard = 0
    total_easy = 0
    total_hard = 0
    wrong = []

    for uid in sorted(truth.keys()):
        predicted = predictions.get(uid)
        gt = truth[uid]
        m = meta[uid]
        difficulty = m["difficulty"]

        if difficulty == "easy":
            total_easy += 1
        else:
            total_hard += 1

        is_correct, error_pct = score_answer(predicted, gt)

        results.append({
            "uid": uid,
            "predicted": predicted or "",
            "correct": 1 if is_correct else 0,
        })

        if is_correct:
            correct_total += 1
            if difficulty == "easy":
                correct_easy += 1
            else:
                correct_hard += 1
        else:
            error_str = f"{error_pct:.1f}%" if error_pct is not None else "N/A"
            wrong.append((uid, difficulty, predicted or "(no answer)", gt, error_str, m["question"]))

    total = len(truth)
    print(f"Score: {correct_total}/{total} ({100*correct_total/total:.1f}%)")
    print(f"Easy:  {correct_easy}/{total_easy} ({100*correct_easy/total_easy:.1f}%)")
    print(f"Hard:  {correct_hard}/{total_hard} ({100*correct_hard/total_hard:.1f}%)")
    print()

    # Write scored results for compare_runs.py
    output_path = results_path.replace(".csv", "_scored.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["uid", "predicted", "correct"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Scored results written to: {output_path}")

    # Show worst failures
    if wrong:
        print(f"\nWrong answers ({len(wrong)}):")
        # Sort by error magnitude (largest first), N/A last
        wrong.sort(key=lambda x: float(x[4].rstrip("%")) if x[4] != "N/A" else 99999, reverse=True)
        for uid, diff, pred, gt, err, q in wrong[:20]:
            print(f"  [{diff}] {uid}: predicted={pred}, truth={gt}, error={err}")
            print(f"         {q}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/local_score.py results.csv [officeqa_full.csv]")
        sys.exit(1)

    oqa = sys.argv[2] if len(sys.argv) > 2 else None
    main(sys.argv[1], oqa)
