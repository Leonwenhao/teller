#!/usr/bin/env python3
"""Standalone evaluation — run OfficeQA questions WITHOUT Arena CLI.

Uses Docker directly + OpenHands SDK to evaluate questions against the
Treasury Bulletin corpus. Scores answers using the official reward function.

Prerequisites:
    - Docker running
    - OpenRouter API key (export OPENROUTER_API_KEY=...)
    - pip install openhands-sdk  (or the script installs it in the container)

Usage:
    # Run all 246 questions
    python3 scripts/standalone_eval.py

    # Run specific questions
    python3 scripts/standalone_eval.py --filter uid0023,uid0041,uid0097

    # Run first N questions
    python3 scripts/standalone_eval.py --limit 20

    # Resume from where you left off
    python3 scripts/standalone_eval.py --resume
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
CSV_PATH = PROJECT_DIR / "officeqa_full.csv"
SKILLS_DIR = PROJECT_DIR / "skills"
RESULTS_FILE = PROJECT_DIR / "results" / "standalone_results.json"
CORPUS_IMAGE = "ghcr.io/sentient-agi/harbor/officeqa-corpus:latest"
MODEL = "openrouter/minimax/minimax-m2.5"


def load_questions(filter_uids=None, limit=None):
    """Load questions from CSV."""
    with open(CSV_PATH) as f:
        questions = list(csv.DictReader(f))
    if filter_uids:
        filter_set = {u.lower().replace("uid", "") for u in filter_uids}
        questions = [q for q in questions if q["uid"].lower().replace("uid", "") in filter_set]
    if limit:
        questions = questions[:limit]
    return questions


def load_skills():
    """Read all skills files and concatenate."""
    skills_content = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            skills_content.append(f"# Skill: {skill_dir.name}\n\n{skill_file.read_text()}")
    return "\n\n---\n\n".join(skills_content)


def build_instruction(question_text):
    """Build the full instruction with corpus info."""
    return question_text + """

## Available Resources

You have access to the full U.S. Treasury Bulletin corpus at `/app/corpus/`. This directory contains 697 parsed Treasury Bulletin text files (Markdown with tables), one per monthly bulletin issue.

**Corpus location:** `/app/corpus/`
**File naming convention:** `treasury_bulletin_YYYY_MM.txt` (e.g., `treasury_bulletin_1941_01.txt`)
**File listing:** `/app/corpus/index.txt`

You must search through these files to find the relevant information to answer the question.

## Output

Write your final answer to `/app/answer.txt`. Numerical answers should be precise (scoring uses 1% tolerance).
"""


def run_question_docker(uid, instruction, skills_text, api_key, timeout=600):
    """Run a single question using Docker + OpenHands SDK."""
    container_name = f"officeqa-{uid.lower()}-{int(time.time())}"

    # Write skills to a temp file to mount
    skills_dir = Path(f"/tmp/officeqa-skills-{uid.lower()}")
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Copy skills directory structure
    for skill_subdir in SKILLS_DIR.iterdir():
        if skill_subdir.is_dir():
            target = skills_dir / skill_subdir.name
            target.mkdir(exist_ok=True)
            skill_file = skill_subdir / "SKILL.md"
            if skill_file.exists():
                (target / "SKILL.md").write_text(skill_file.read_text())

    # Create the agent runner script
    runner_script = skills_dir / "run_standalone.py"
    runner_script.write_text(f'''#!/usr/bin/env python3
"""Standalone OpenHands SDK agent runner."""
import os
import sys

# Install openhands-sdk if not present
try:
    import openhands_sdk
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openhands-sdk", "-q"])
    import openhands_sdk

from openhands_sdk import Agent

def main():
    instruction = """{instruction.replace('"', '\\"').replace("'", "\\'")}"""

    # Load skills
    skill_paths = []
    skills_base = "/tmp/skills"
    if os.path.exists(skills_base):
        for d in sorted(os.listdir(skills_base)):
            skill_path = os.path.join(skills_base, d, "SKILL.md")
            if os.path.exists(skill_path):
                skill_paths.append(os.path.join(skills_base, d))

    agent = Agent(
        model="{MODEL}",
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        skill_paths=skill_paths if skill_paths else None,
    )

    result = agent.run(instruction)
    print(f"Agent completed. Cost: ${{result.cost:.4f}}")

if __name__ == "__main__":
    main()
''')

    # Run Docker container with corpus + agent
    docker_cmd = [
        "docker", "run", "--rm",
        "--name", container_name,
        "-e", f"LLM_API_KEY={api_key}",
        "-e", "LLM_BASE_URL=https://openrouter.ai/api/v1",
        "-e", f"LLM_MODEL={MODEL}",
        "-v", f"{skills_dir}:/tmp/skills:ro",
        "-v", f"{runner_script}:/tmp/run_standalone.py:ro",
        "--memory", "4g",
        CORPUS_IMAGE,
        "bash", "-c",
        "pip install openhands-sdk -q 2>/dev/null && "
        f"python3 /tmp/run_standalone.py && "
        "cat /app/answer.txt 2>/dev/null || echo '__NO_ANSWER__'"
    ]

    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()

        # Extract the answer (last line that's not a log message)
        lines = output.strip().split("\n")
        answer = lines[-1] if lines else "__NO_ANSWER__"

        # If the answer is a log line, try to find the actual answer
        if answer.startswith("[") or answer.startswith("Agent") or answer.startswith("pip"):
            answer = "__NO_ANSWER__"

        return {
            "answer": answer,
            "stdout": output[-500:],  # Last 500 chars
            "stderr": result.stderr[-500:] if result.stderr else "",
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "kill", container_name], capture_output=True)
        return {"answer": "__TIMEOUT__", "stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"answer": "__ERROR__", "stdout": "", "stderr": str(e), "returncode": -1}
    finally:
        # Cleanup
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        import shutil
        shutil.rmtree(skills_dir, ignore_errors=True)


def score_answer(expected, predicted, tolerance=0.01):
    """Score an answer using fuzzy numeric matching (1% tolerance)."""
    if not predicted or predicted in ("__NO_ANSWER__", "__TIMEOUT__", "__ERROR__"):
        return 0.0

    # Try importing the official reward function
    try:
        sys.path.insert(0, str(PROJECT_DIR))
        from reward import score_answer as official_score
        return official_score(expected, predicted, tolerance)
    except ImportError:
        pass

    # Fallback: simple numeric comparison
    try:
        # Clean both values
        def clean_num(s):
            s = s.strip().replace(",", "").replace("%", "").replace("$", "")
            s = re.sub(r'[^\d.\-]', '', s)
            return float(s)

        exp = clean_num(expected)
        pred = clean_num(predicted)

        if exp == 0:
            return 1.0 if abs(pred) < tolerance else 0.0
        return 1.0 if abs((pred - exp) / exp) <= tolerance else 0.0
    except (ValueError, ZeroDivisionError):
        # String comparison fallback
        return 1.0 if expected.strip().lower() == predicted.strip().lower() else 0.0


def load_existing_results():
    """Load previously saved results for resume support."""
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    return {}


def save_results(results):
    """Save results to JSON."""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps(results, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Standalone OfficeQA evaluation")
    parser.add_argument("--filter", type=str, help="Comma-separated UIDs to test")
    parser.add_argument("--limit", type=int, help="Max questions to run")
    parser.add_argument("--resume", action="store_true", help="Skip already-scored questions")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout per question (seconds)")
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: Set OPENROUTER_API_KEY environment variable")
        sys.exit(1)

    # Check Docker
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        print("ERROR: Docker is not running")
        sys.exit(1)

    # Pull corpus image
    print(f"Ensuring corpus image is available: {CORPUS_IMAGE}")
    subprocess.run(["docker", "pull", CORPUS_IMAGE], capture_output=True)

    # Load questions
    filter_uids = args.filter.split(",") if args.filter else None
    questions = load_questions(filter_uids, args.limit)
    print(f"Loaded {len(questions)} questions")

    # Load existing results for resume
    existing = load_existing_results() if args.resume else {}
    skills_text = load_skills()

    passed = 0
    failed = 0
    skipped = 0
    total_cost = 0
    results = existing.copy()

    for i, q in enumerate(questions):
        uid = q["uid"]

        if args.resume and uid.lower() in {k.lower() for k in existing}:
            prev = existing.get(uid, existing.get(uid.lower(), {}))
            if prev.get("scored"):
                if prev.get("correct"):
                    passed += 1
                else:
                    failed += 1
                skipped += 1
                continue

        print(f"\n[{i+1}/{len(questions)}] {uid} ({q.get('difficulty', '?')})...")

        instruction = build_instruction(q["question"])
        result = run_question_docker(uid, instruction, skills_text, api_key, args.timeout)

        reward = score_answer(q["answer"], result["answer"])
        correct = reward > 0

        if correct:
            passed += 1
            print(f"  ✓ PASS (answer: {result['answer'][:50]})")
        else:
            failed += 1
            print(f"  ✗ FAIL (got: {result['answer'][:50]}, expected: {q['answer'][:50]})")

        results[uid] = {
            "scored": True,
            "correct": correct,
            "reward": reward,
            "agent_answer": result["answer"],
            "expected_answer": q["answer"],
            "difficulty": q.get("difficulty", ""),
            "question": q["question"][:200],
        }

        # Save after each question (resume support)
        save_results(results)

    total = passed + failed
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed}/{total} correct ({passed/total*100:.1f}%)")
    print(f"Skipped (resumed): {skipped}")
    print(f"Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
