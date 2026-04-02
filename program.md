# OfficeQA Skills Optimization — Autonomous Research Loop

This is an autonomous experiment loop to improve an AI coding agent's accuracy on the OfficeQA benchmark (246 questions about U.S. Treasury Bulletin documents). Inspired by [Karpathy's AutoResearch](https://github.com/karpathy/autoresearch).

## Context

We're competing in **Sentient Arena Cohort 0**. A pre-built coding agent (OpenHands SDK + MiniMax M2.5 model) runs against 246 questions. We can only modify **skills files** — markdown instructions that get injected into the agent's system prompt. The agent reads these skills, then searches a corpus of 697 Treasury Bulletin documents, extracts data from tables, computes answers in Python, and writes to `/app/answer.txt`.

**Current baseline:** ~155 correct out of 246 (~63% accuracy).  
**Target:** 175+ correct (71%+ accuracy).  
**Score to beat:** 182.1 (#1 on leaderboard, 68.7% accuracy).

## Setup

1. **Prerequisites:** Docker must be running. An OpenRouter API key is required.

2. **Configure:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenRouter API key (MUST have 'export' prefix)
   ```

3. **Pull the corpus Docker image** (public, ~2GB, has all 697 Treasury Bulletins):
   ```bash
   docker pull ghcr.io/sentient-agi/harbor/officeqa-corpus:latest
   ```

4. **Read the in-scope files** for full context:
   - `skills/methodology/SKILL.md` — Core agent instructions (pipeline, formatting, speed)
   - `skills/known_pitfalls/SKILL.md` — Error prevention rules (units, dates, terminology)
   - `skills/computation_patterns/SKILL.md` — Python code patterns (regression, Theil, CAGR)
   - `skills/retrieval_strategy/SKILL.md` — How to search the document corpus
   - `skills/table_parsing_guide/SKILL.md` — How to read Treasury Bulletin tables
   - `officeqa_full.csv` — All 246 questions with ground truth answers
   - `arena.yaml` — Agent configuration (DO NOT change harness or model)

5. **Establish baseline** by running a subset:
   ```bash
   source .env && python3 scripts/standalone_eval.py --limit 20
   ```

6. **Initialize results.tsv:**
   ```
   experiment	correct	total	accuracy	status	description
   ```

## What You CAN Modify

**Skills files only.** These are the 5 files in `skills/*/SKILL.md`:
- `methodology/SKILL.md` — Execution rules, question classification, pipeline phases
- `known_pitfalls/SKILL.md` — Error patterns and prevention rules  
- `computation_patterns/SKILL.md` — Python code templates for computations
- `retrieval_strategy/SKILL.md` — Document search strategy
- `table_parsing_guide/SKILL.md` — Table structure navigation

These files are injected verbatim into the agent's system prompt. Every word matters. The agent (MiniMax M2.5) reads these before answering each question.

## What You CANNOT Modify

- `arena.yaml` — The harness (`openhands-sdk`) and model (`minimax/minimax-m2.5`) are fixed by competition rules
- The evaluation harness, Docker setup, or corpus
- `officeqa_full.csv` — Ground truth answers
- `scripts/*.py` — Evaluation infrastructure

## The Goal

**Maximize the number of correctly answered questions out of 246.** Scoring uses 1% fuzzy numeric tolerance. A correct answer scores 1.0, incorrect scores 0.0.

## Critical Lessons Learned (READ BEFORE STARTING)

These are hard-won insights from weeks of iteration. Violating them WILL cause regressions:

1. **MORE instructions ≠ MORE accuracy.** We proved this twice:
   - v3 prompt (172 lines) scored WORSE than v2 (148 lines)
   - v7 skills (631 lines) scored WORSE than v6 (543 lines)
   - The agent gets confused by verbose instructions and spends more time reading, less executing
   - **Keep skills CONCISE. Every line must earn its place.**

2. **There is ±5 question variance per run.** The same config can score 153 or 158 depending on run. To confirm an improvement is real, it needs to be >5 questions better. Small changes (+1-2) are noise.

3. **Cost matters for the final Arena score** (not for local eval). The multiplier penalizes cost. Instructions that make the agent "more thorough" (more tool calls, re-reading files) increase cost and hurt the final score even if accuracy improves slightly.

4. **The 5 known failure modes** (in priority order):
   - Table parsing errors — hierarchical headers cause column shifts
   - Unit confusion — values in thousands/millions/billions, question asks for different unit
   - Fiscal year vs calendar year — U.S. fiscal year starts October (post-1976)
   - Document versioning — same data revised across bulletin issues
   - External knowledge — ~13% of questions need web search (country groupings, definitions)

5. **The agent (MiniMax M2.5) has specific weaknesses:**
   - Ignores long instruction blocks — keep critical rules at the TOP of each file
   - Bad at complex formulas from memory — must provide exact Python code
   - Runs out of steps on multi-file extractions — needs batch retrieval patterns
   - Sometimes doesn't write answer.txt — loses entire question score

## Evaluation (Standalone — No Arena CLI Needed)

**Fast eval (20 questions, ~20 min, ~$1):**
```bash
source .env && python3 scripts/standalone_eval.py --limit 20
```

**Targeted eval (specific questions):**
```bash
source .env && python3 scripts/standalone_eval.py --filter uid0041,uid0097,uid0127
```

**Full eval (246 questions, ~4 hours, ~$12):**
```bash
source .env && python3 scripts/standalone_eval.py
```

**Resume after interruption:**
```bash
source .env && python3 scripts/standalone_eval.py --resume
```

Results are saved to `results/standalone_results.json` after each question (survives crashes).
View results:
```bash
python3 -c "
import json
d = json.load(open('results/standalone_results.json'))
passed = sum(1 for v in d.values() if v.get('correct'))
total = sum(1 for v in d.values() if v.get('scored'))
print(f'Passed: {passed}/{total} ({passed/total*100:.1f}%)')
for uid, v in sorted(d.items()):
    m = '✓' if v.get('correct') else '✗'
    print(f'  {m} {uid} [{v.get(\"difficulty\",\"?\")}] got={v.get(\"agent_answer\",\"?\")[:30]} exp={v.get(\"expected_answer\",\"?\")[:30]}')
"
```

## The Experiment Loop

LOOP FOREVER:

1. **Analyze current failures:** Look at which questions fail and WHY. Read the question from `officeqa_full.csv`, understand what the agent needs to do, and identify the failure pattern.

2. **Form a hypothesis:** "If I add/modify X in the skills, it will fix failure pattern Y which affects ~N questions."

3. **Make a SMALL, targeted edit** to one or two skills files. Do NOT rewrite everything. Change one thing at a time so you can attribute the result.

4. **git commit** the change with a descriptive message.

5. **Run evaluation** (use a representative subset of ~20-30 questions for speed):
   ```bash
   source .env && python3 scripts/standalone_eval.py --limit 20
   ```
   Or test specific failure cases:
   ```bash
   source .env && python3 scripts/standalone_eval.py --filter uid0041,uid0097,uid0127
   ```

6. **Extract results:**
   ```bash
   python3 -c "
   import json
   d = json.load(open('results/standalone_results.json'))
   passed = sum(1 for v in d.values() if v.get('correct'))
   total = sum(1 for v in d.values() if v.get('scored'))
   print(f'{passed}/{total} correct ({passed/total*100:.1f}%)')
   "
   ```

7. **Log to results.tsv:**
   ```
   exp-N	14	20	70.0%	keep	added explicit Theil index warning
   ```

8. **Decision:**
   - If accuracy improved by >1 question: **KEEP** (advance the branch)
   - If accuracy is same or worse: **REVERT** (`git reset --hard HEAD~1`)
   - If accuracy improved on targets but regressed elsewhere: **REVERT** (net negative)

9. **Repeat.** Each experiment takes ~20 min. You can run ~3/hour, ~70 overnight.

## Useful Ground Truth Patterns

From `officeqa_full.csv`, the 246 questions break down as:
- 113 easy, 133 hard
- ~30-40% involve multi-value extraction or time series
- ~20% need unit conversion
- ~15% involve fiscal year handling  
- ~10% need statistical computation (regression, Theil, t-test)
- ~7% require external knowledge (web search)
- ~3% reference charts/visuals (unfixable from text)

## Budget

Be mindful of API costs. Each 20-question eval costs ~$1 via OpenRouter. The API key has limited credits. Prefer targeted tests (`--filter`) when debugging a specific question, and full 20-question sweeps to confirm improvements.

## NEVER STOP

Once the experiment loop has begun, do NOT pause to ask the human if you should continue. The human might be asleep. You are autonomous. If you run out of ideas, re-read the failure patterns, try combining previous near-misses, try more radical approaches (restructuring skills entirely, different instruction ordering, removing sections). The loop runs until the human interrupts you.
