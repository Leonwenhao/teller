# Codex Analysis Request — Sentient Arena Strategy

You are being asked to review a competition progress document and provide your analysis and recommendations. Read the file `notes/session8_progress.md` thoroughly, then write your analysis to `notes/codex_analysis.md`.

## Context
We're competing in Sentient Arena Cohort 0 — a benchmark competition where teams configure an AI coding agent (OpenHands SDK + MiniMax M2.5 model) to answer 246 grounded reasoning questions about U.S. Treasury Bulletin documents. We can only modify **skills files** (markdown instructions injected into the agent's system prompt) and **agent config** (arena.yaml settings).

**Current standing:** #4 with 180.9 score (173/246 correct, 70.3% accuracy, $19.30 cost)
**Leader:** 188 score. We need 190+ to win.
**Deadline:** April 11, 2026 (8 days remaining)

## Your Task

Read `notes/session8_progress.md` and write `notes/codex_analysis.md` containing:

### 1. Assessment of Our Approach
- What did we do right? What did we do wrong?
- Are we on the right track or do we need a fundamentally different approach?
- Comment on the "addition by subtraction" finding — is it generalizable or specific to MiniMax M2.5?

### 2. The Cost-Accuracy Tradeoff
- We get MORE correct answers than #1 (173 vs ~176) but score lower due to higher cost ($19.30 vs ~$14)
- max_iterations=100 is essential for accuracy but expensive
- How would you solve this? Specific, actionable suggestions.

### 3. Strategy to Hit 190
- The math: 190 requires ~178 correct at $14 cost, or ~185 correct at $18 cost
- Given our failure analysis (30 real wrong answers, 114 timeouts), what's the highest-EV path?
- Should we focus on fixing wrong answers or reducing cost?

### 4. Specific Recommendations
- Should we trim skills to reduce cost per iteration?
- What max_iterations value would you test? (100 works, default doesn't, what about 50/75?)
- Are there structural changes (MCP servers, different retrieval) worth attempting in 8 days?
- Any prompt engineering techniques specifically effective for MiniMax M2.5?

### 5. Answer the 12 Questions
In the progress document there are 12 numbered questions under "Questions and Discussion Points for Codex". Please address each one.

### 6. Wild Card Ideas
- Anything we haven't considered?
- What would you try if you had 8 days and $161 in API credits?
- How would you approach the variance problem (±15 questions between identical runs)?

## Key Files to Reference
- `notes/session8_progress.md` — The full progress report (READ THIS FIRST)
- `skills/methodology/SKILL.md` — Current agent methodology (103 lines)
- `skills/known_pitfalls/SKILL.md` — Error prevention rules (150 lines)
- `skills/computation_patterns/SKILL.md` — Python formula patterns (146 lines)
- `skills/retrieval_strategy/SKILL.md` — Search strategy (42 lines)
- `skills/table_parsing_guide/SKILL.md` — Table navigation (102 lines)
- `arena.yaml` — Current agent config
- `officeqa_full.csv` — All 246 questions with ground truth
- `results/complete_246_results.json` — Local test results (245 questions)

## Output
Write your complete analysis to `notes/codex_analysis.md` as a well-structured markdown document. Be specific, actionable, and opinionated. Don't hedge — tell us what to do.
