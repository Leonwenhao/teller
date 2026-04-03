# Cold Start — Session 9

## Who You Are
You're helping Leon (柳文浩) from Dolores Research compete in Sentient Arena Cohort 0. Read CLAUDE.md for full context.

## Where We Left Off
- **Leaderboard:** #4 with 180.9 score (173/246 correct, 70.3% accuracy)
- **Leader:** 188 score — we need 190+ to win
- **Deadline:** April 11, 2026
- **Best config:** v12 (skills with scipy one-liner + max_iterations=100)
- **Budget:** ~$150 OpenRouter remaining, 5 Arena submissions/day (free)

## What to Do First

### 1. Sanity Check
```bash
source .env && arena leaderboard
cat arena.yaml
wc -l skills/*/SKILL.md
```

### 2. Read Codex's Analysis
```bash
cat notes/codex_analysis.md
```
Codex was asked to review our progress and suggest a path to 190. Its analysis covers:
- Assessment of our approach
- The cost-accuracy tradeoff
- Specific recommendations and strategy
- Answers to 12 questions we posed

### 3. Key Decision Point
The core tension: `max_iterations: 100` gives us 173 correct but costs $19.30. Without it, accuracy drops to 155. The leader gets ~176 correct at ~$14 cost.

Options to explore:
- **max_iterations=50 or 75** — find the sweet spot between accuracy and cost
- **Trim skills** to reduce cost per iteration while keeping guardrails
- **Structural changes** (MCP servers, different retrieval) if Codex recommends them

## Key Files
- `notes/session8_progress.md` — Full progress report from last session
- `notes/codex_analysis.md` — Codex's strategic analysis and recommendations
- `notes/codex_coldstart_prompt.md` — The prompt used to generate Codex analysis
- `results/complete_246_results.json` — Local test results for 245 questions
- `officeqa_full.csv` — All 246 questions with ground truth
- `SCRATCHPAD.md` — Full session history (update at end of session)

## The Proven Rules
1. **Adding skills content ALWAYS regresses** — v7 and v9 both lost 15+ correct answers
2. **Sharpening existing rules works** — v8 write-early gained +9, v12 scipy gained +6
3. **max_iterations=100 is load-bearing** — removing it lost 18 correct answers
4. **±15 question variance per run** — same config can score 152 or 167
5. **Cost is the bottleneck** — we have more correct answers than #1 but lose on multiplier

## Submission History (all scores under current system)
| Tag | Score | Correct | Cost | Key |
|-----|-------|---------|------|-----|
| **v12 scipy+iter** | **180.9** | **173** | **$19.30** | **BEST — scipy + max_iter=100** |
| v8 write-early | 178.7 | 167 | $15.00 | Write answer immediately |
| v11 mcp+cfg | 173.5 | 164 | $17.72 | MCP web-search (partially crashed) |
| v10 trimmed | 172.7 | 165 | $19.47 | 251 lines (too lean) |
| v9 formulas | 163.7 | 152 | $12.22 | Added formulas → REGRESSED |
| v13 scipy only | 162.5 | 155 | $19.36 | Removed max_iter → REGRESSED |
| v8 revert | 162.5 | 152 | $13.93 | Confirms variance |
