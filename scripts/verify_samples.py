#!/usr/bin/env python3
"""Verify (and optionally fix) the scoring pipeline for all generated samples.

The arena verifier reads config.get("expected_answer") — using "answer" as the
key causes every answer to score 0. This script checks and fixes this.

Usage:
    python3 scripts/verify_samples.py          # Check only
    python3 scripts/verify_samples.py --fix    # Check and fix
"""

import csv
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SAMPLES_DIR = PROJECT_DIR / ".arena" / "samples"
CSV_PATH = PROJECT_DIR / "officeqa_full.csv"


def main():
    fix_mode = "--fix" in sys.argv

    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found.")
        sys.exit(1)

    with open(CSV_PATH) as f:
        qmap = {r["uid"].lower(): r for r in csv.DictReader(f)}

    broken = 0
    fixed = 0
    missing_instruction = 0
    total = 0

    for d in sorted(SAMPLES_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith("officeqa-"):
            continue

        cfg = d / "tests" / "config.json"
        if not cfg.exists():
            continue

        total += 1
        data = json.loads(cfg.read_text())

        # Check expected_answer key
        if "expected_answer" not in data:
            broken += 1
            if fix_mode:
                uid = d.name.replace("officeqa-", "")
                q = qmap.get(uid, {})
                data["expected_answer"] = q.get("answer", data.get("answer", ""))
                cfg.write_text(json.dumps(data, indent=2))
                fixed += 1

        # Check instruction.md exists
        if not (d / "instruction.md").exists():
            missing_instruction += 1

    status = "PASS" if broken == 0 else ("FIXED" if fix_mode and broken == fixed else "FAIL")
    print(f"[{status}] {SAMPLES_DIR}")
    print(f"  Total samples: {total}")
    print(f"  Broken configs (missing expected_answer): {broken}")
    if fix_mode:
        print(f"  Fixed: {fixed}")
    if missing_instruction:
        print(f"  Missing instruction.md: {missing_instruction}")

    if broken > 0 and not fix_mode:
        print(f"\n  Run with --fix to repair: python3 scripts/verify_samples.py --fix")
        sys.exit(1)
    elif broken == 0:
        print(f"\n  All samples verified. Scoring pipeline is correct.")


if __name__ == "__main__":
    main()
