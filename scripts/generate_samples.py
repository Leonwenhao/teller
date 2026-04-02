#!/usr/bin/env python3
"""Generate arena-compatible sample directories for all 246 OfficeQA questions.

Adapted from arena-toolkit by Ground Wire team.
Uses an existing arena sample as template and creates properly formatted
sample directories that the arena CLI can evaluate.

IMPORTANT: Each sample's tests/config.json must have 'expected_answer' (not 'answer').
The arena verifier reads config.get("expected_answer") — using the wrong key causes
every answer to score 0 regardless of correctness.
"""

import csv
import json
import os
import re
import shutil
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SAMPLES_DIR = PROJECT_DIR / ".arena" / "samples"
CSV_PATH = PROJECT_DIR / "officeqa_full.csv"


def find_template():
    """Find an existing arena sample to use as template."""
    for d in SAMPLES_DIR.iterdir():
        if d.is_dir() and (d / "tests" / "evaluate.py").exists():
            return d
    return None


def main():
    if not SAMPLES_DIR.exists():
        print("ERROR: .arena/samples/ not found. Run 'arena pull' first.")
        sys.exit(1)

    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Download it first:")
        print("  curl -O https://raw.githubusercontent.com/databricks/officeqa/main/officeqa_full.csv")
        sys.exit(1)

    template = find_template()
    if not template:
        print("ERROR: No valid template sample found. Run 'arena pull' to get the original samples.")
        sys.exit(1)

    print(f"Using template: {template.name}")

    with open(CSV_PATH) as f:
        questions = list(csv.DictReader(f))

    print(f"Loaded {len(questions)} questions from CSV")

    existing = set(d.name for d in SAMPLES_DIR.iterdir() if d.is_dir())
    generated = 0
    skipped = 0

    for q in questions:
        uid = q["uid"]
        sample_name = f"officeqa-{uid.lower()}"

        if sample_name in existing:
            # Still update the config.json to ensure expected_answer is correct
            cfg_path = SAMPLES_DIR / sample_name / "tests" / "config.json"
            if cfg_path.exists():
                config = json.loads(cfg_path.read_text())
                if "expected_answer" not in config:
                    config["expected_answer"] = q["answer"]
                    cfg_path.write_text(json.dumps(config, indent=2))
                    print(f"  Fixed config for existing {sample_name}")
            skipped += 1
            continue

        sample_dir = SAMPLES_DIR / sample_name
        shutil.copytree(template, sample_dir)

        # Write the question as instruction.md
        instruction = q["question"] + """

## Available Resources

You have access to the full U.S. Treasury Bulletin corpus at `/app/corpus/`. This directory contains 697 parsed Treasury Bulletin text files (Markdown with tables), one per monthly bulletin issue.

**Corpus location:** `/app/corpus/`
**File naming convention:** `treasury_bulletin_YYYY_MM.txt` (e.g., `treasury_bulletin_1941_01.txt`)
**File listing:** `/app/corpus/index.txt`

You must search through these files to find the relevant information to answer the question.

## Output

Write your final answer to `/app/answer.txt`. Numerical answers should be precise (scoring uses 1% tolerance).
"""
        (sample_dir / "instruction.md").write_text(instruction)

        # Update task.toml
        toml = (sample_dir / "task.toml").read_text()
        toml = re.sub(r'source_id = "[^"]*"', f'source_id = "{uid}"', toml)
        # Remove template-specific source_files/source_docs
        lines = [l for l in toml.split("\n")
                 if "source_files" not in l and "source_docs" not in l]
        (sample_dir / "task.toml").write_text("\n".join(lines))

        # Write solution
        solution_dir = sample_dir / "solution"
        solution_dir.mkdir(exist_ok=True)
        (solution_dir / "solve.sh").write_text(
            f'#!/bin/bash\nset -e\necho "Writing oracle answer..."\n'
            f'cat > /app/answer.txt << \'EOF\'\n{q["answer"]}\nEOF\n'
            f'echo "Answer written to /app/answer.txt"\ncat /app/answer.txt\n'
        )

        # Write config.json with CORRECT key: expected_answer
        config = {
            "uid": uid,
            "question": q["question"],
            "expected_answer": q["answer"],
            "difficulty": q.get("difficulty", ""),
            "tolerance": 0.01,
            "source_docs": [s.strip() for s in q.get("source_docs", "").split(",") if s.strip()],
            "source_files": [s.strip() for s in q.get("source_files", "").split(",") if s.strip()],
        }
        (sample_dir / "tests" / "config.json").write_text(json.dumps(config, indent=2))

        generated += 1

    total = len([d for d in SAMPLES_DIR.iterdir() if d.is_dir()])
    print(f"\nGenerated {generated} new samples, skipped {skipped} existing.")
    print(f"Total: {total} sample directories in .arena/samples/")


if __name__ == "__main__":
    main()
