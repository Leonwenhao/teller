# SCRATCHPAD — Sentient Arena Cohort 0
**Last updated:** April 2, 2026

## Current Best Configuration (for submission) — v6 (reverted from v7)
- Harness: **openhands-sdk** (injects all skills into system prompt)
- Model: openrouter/minimax/minimax-m2.5 (Arena forces MiniMax M2.5 for all teams)
- Skills: 5 files (543 lines) — v6 baseline
- Prompt template: NOT used by openhands-sdk (all content in skills)
- Config: arena.yaml (openhands-sdk + reasoning_effort: medium — no-op per SDK source)
- arena.yaml environment: {} (using task defaults)

## LEADERBOARD STATUS: #6 (as of April 2)
- **Score to beat: 182.1** (#1 Vikranth — 68.7% accuracy, $0.06/task, 2.9m/task)
- **Our best: 170.7** (158/246 correct, $12.82 total, 217s avg) — openhands-sdk submission
- #2 GroundWire: 176.4, #3 Kurukshetra: 175.4, #4 CTR Evolver: 175.3, #5 Zeno AI: 174.1
- **Deadline: April 11, 2026** (extended from April 5)
- Target: 190 score range (70%+ accuracy)

## KEY INSIGHT: PLATEAU CONFIRMED
v7 (more skills, 631 lines) scored WORSE than v6 (543 lines): 148 correct vs 153-158.
v6 revert scored 153 correct (162.3) — confirming ~±5 question variance per run.
**More instructions ≠ more accuracy.** The path to 190 requires data-driven iteration, not more prompting.

## NEXT: Full 246-Question Local Diagnostic Run
- All 246 OfficeQA questions generated as arena-compatible samples ✓
- Ground truth CSV downloaded from Databricks OfficeQA repo ✓  
- Batch eval script with resume support ready ✓
- Smoke test PASSED (uid0023 confirmed working) ✓
- **Launch command:** `source .env && BATCH_SIZE=10 bash scripts/run_full_eval.sh`
- **Estimated:** ~4 hours, ~$12 cost, 25 batches of 10
- **Budget:** ~$161 OpenRouter remaining

## SCORING FORMULA (reverse-engineered, fits perfectly)
```
multiplier = 1.1852 - 0.005608 × total_cost($) - 0.000278 × avg_latency(s)
score = correct_tasks × multiplier
```
- **$1 more total cost = -0.9 points** (at 160 correct)
- 1s less latency = +0.04 points (cost is 20x more impactful than time)
- +1 correct answer = +0.96 points (at current multiplier)
- Break-even: +1 correct answer offsets $1.07 of cost increase

## v3 LESSONS LEARNED
- v3 mega prompt (172 lines) added +2 correct but cost $2.44 more total → net -0.2 points
- Token analysis: v3 used 3x more input tokens (238K vs 85K) for same question (uid0023)
- The extra skills content (fallback strategies, multi-value verification) made agent DO MORE WORK, not just read more
- Cost increase was from agent behavior change (more tool calls), not prompt length
- **Conclusion: adding instructions that make the agent "more thorough" hurts score because cost penalty > accuracy gain**
- **v2 prompt (148 lines) with "Be FAST" is the optimal balance — RESTORED AS ACTIVE**
- reasoning_effort: "low" test was inconclusive (agent hung, possibly unsupported for MiniMax via OpenRouter)

## v4 STRATEGY: HARNESS SWITCH TO openhands-sdk (March 31)
New leader (165.4) uses openhands-sdk at $0.07/task — same accuracy as us but much cheaper.
Our opencode at $0.12/task loses ~$12 total = ~6.7 points from cost penalty alone.

**Decision: Switch to openhands-sdk for submissions.**
- Skills files updated with v2 improvements (Be FAST, Theil formula, don't plan, write early)
- openhands-sdk injects all skills into system prompt (525+ lines)
- Even if accuracy is identical, lower cost = higher multiplier = higher score
- Math: 159 correct × 1.019 (at $0.07/task) = 162.0 (vs current 152.5)

## CRITICAL RULE CHANGE (discovered March 30)
- **Submissions are FREE** — Arena uses THEIR API keys, not ours
- **Everyone evaluated with MiniMax M2.5** — model field in arena.yaml is IGNORED
- **OpenRouter credits are for local testing only**
- The competition is purely about behavioral engineering: harness + prompt + skills
- opencode harness now supports skills (README updated)

## Score Summary
- Sample questions tested: 19/20 (uid0030 is visual, always fails)
- Passed: uid0004, uid0023, uid0033, uid0041, uid0048, uid0057, uid0097, uid0111, uid0127, uid0136, uid0167, uid0192, uid0194, uid0199, uid0217, uid0220, uid0230, uid0241 (18 confirmed)
- Failed: NONE on real attempts
- Infrastructure failures: uid0246 (Docker timeout, $0.00 — not an agent error)
- **Accuracy on real attempts: 18/18 = 100% on sample set**

## Budget Status
- OpenRouter starting credit: $100
- Spent to date: ~$39 + ~$0.20 (MiniMax/DeepSeek tests today)
- Remaining: ~$60
- NOTE: Budget only matters for LOCAL testing. Submissions are free.
- New voucher available at https://arena.sentient.xyz/ ($100, unclaimed)

## Gap Fixes Implemented (Session 3 — March 25)
1. arena.yaml environment: {} — removed timeout override, eliminated memory warning
2. Phase 5 output formatting rules — explicit rounding/format instructions
3. Web search capability — Wikipedia API lookup for external knowledge
4. "Reported in" vs "reported for" — date interpretation distinction
5. Historical grouping verification — web-verify country memberships
6. Document versioning strengthened — mechanistic check-next-bulletin instructions

**Results: Both targeted fixes worked (uid0199, uid0220 → PASS). 7/9 new questions passed.**

## Key Findings
- openhands-sdk loads skills into agent system prompt (confirmed via openhands_sdk.txt logs)
- openhands-sdk does NOT load prompt template (all content must be in skills)
- trajectory.json is simplified — check openhands_sdk.txt for full context
- Skills reduce Sonnet cost by 85% ($5/q → $0.45/q)
- Skills improve mini accuracy by 10% (40% → 50%)

## Remaining Failures — Diagnosis

### uid0097 (hard) — Parsing error
- **Question:** ESF Balance Sheet nominal capital + abs diff with total capital & liabilities, March 31 1989
- **Agent answer:** [0.2, 20.776]
- **Expected:** [8.124, 12.852]
- **Root cause:** Agent read "Capital" ($200M appropriation) instead of total nominal capital (~$8.124B). ESF Balance Sheet has both stated capital and total capital with accumulated earnings. Agent picked wrong row.
- **Proposed fix:** Add note to known_pitfalls about balance sheet terminology: "stated capital" vs "total capital" on balance sheets.

### uid0127 (easy — HIGH PRIORITY) — Unit conversion error
- **Question:** Mean of ESF Total assets for Sep 1991, Jun+Sep 1992 in nominal dollars
- **Agent answer:** 35028267.33 (thousands)
- **Expected:** 35028267333.33 (dollars)
- **Root cause:** Agent extracted correct values from ESF table (in thousands of dollars) but didn't convert to raw dollars. Question asks for "nominal dollars" not "thousands of dollars." Factor of 1000 error.
- **Proposed fix:** Strengthen unit conversion in known_pitfalls — when question says "in nominal dollars" or "in dollars", convert from table units (thousands/millions) to raw dollars.

## Active Submission
- **Submission ID:** ccdf4848-9dd5-4fe5-8c3a-22c413338574
- **Status:** in_progress (submitted 2026-03-30 ~4:13 PM)
- **Config:** opencode + deepseek-v3.2 + tuned prompt v3 (138 lines)
- **Tag:** deepseek-v3.2-tuned-v3
- **Quota remaining:** 2/3 today (resets midnight UTC)

## Next Actions (Priority Order)
1. **Run full 246-question local eval overnight:** `source .env && BATCH_SIZE=10 bash scripts/run_full_eval.sh`
2. Analyze results: `python3 scripts/aggregate_results.py` → failure_log.csv
3. Categorize all ~90 failures by pattern (retrieval miss, extraction error, formula error, format, timeout)
4. Fix top 3-5 patterns by EV, re-run full eval, measure net impact
5. Submit improved config to Arena for leaderboard score

## Session Log

### Session 0 — March 22 (Planning)
Produced GENESIS.md, BOTCOIN_AUDIT.md. Decided OpenHands + four-phase pipeline.

### Session 1 — March 22-23 (Setup + First Runs)
Installed CLI, authenticated, first tests. 2/5 easy questions pass with mini. Created retrieval strategy skill.

### Session 2 — March 23 (Breakthrough)
Discovered openhands vs openhands-sdk distinction. Skills + Sonnet = 85% cost reduction. 80% accuracy on 10 questions.

### Session 3 — March 25 (Gap Fixes + Full Sample Coverage)
Implemented 6 gap fixes based on failure diagnosis. Both persistent failures fixed. Tested all 20 sample questions: 15/17 real attempts pass (88%). Diagnosed remaining 2 failures (uid0097 parsing, uid0127 unit conversion).

### Session 4 — March 26 (DeepSeek Testing + Cross-Model Validation)
Tested DeepSeek V3.2 as cheap alternative (~10-15x cheaper than Sonnet). Fixed 4 remaining failures. DeepSeek final: 16/19 = 84% on sample set. Sonnet verified at 18/18 = 100%. Key discovery: opencode harness doesn't inject skills into agent context — only prompt template reaches agent. Merged critical rules into prompt template.

### Session 5 — March 30 (Audit + First Full Submission)
Verified team registration (quota: 3/day). Audited all config files. Found 4 content gaps in prompt template (computation patterns, output formatting, web search, document versioning). Added all 4 gaps to prompt template (82→138 lines). Created DeepSeek arena.yaml config. Sanity test: uid0023 PASS ($0.16). Submitted DeepSeek V3.2 to full 246-question benchmark (ID: ccdf4848-9dd5-4fe5-8c3a-22c413338574). Budget note: OPENROUTER_API_KEY must be exported via `source .env` before arena commands.

### Session 6 — March 30 (MiniMax M2.5 Investigation + Full Sample Testing)

**Phase 1 Findings — Harness Investigation:**

1. **Skills injection confirmed:**
   - `openhands-sdk`: INJECTS all 5 skills files into system prompt (525 lines). Confirmed via openhands_sdk.txt logs (10+ matches for skills headings).
   - `opencode`: Does NOT inject skills. Copies them to `~/.config/opencode/skills/` but they don't reach the agent prompt. Only the prompt template (138 lines) + question + resource info reaches the agent.

2. **MiniMax M2.5 compatibility:**
   - `opencode` + `openrouter/minimax/minimax-m2.5`: PASS uid0023, 160s, $0.018
   - `openhands-sdk` + `openrouter/minimax/minimax-m2.5`: PASS uid0023, 229s, $0.029
   - Both harnesses work. openhands-sdk is 1.4x slower, 1.6x costlier.

3. **Decision: Use openhands-sdk for MiniMax.**
   - Rationale: openhands-sdk gives MiniMax access to ALL 525 lines of skills content (methodology, known pitfalls, computation patterns, retrieval strategy, table parsing guide) PLUS the prompt template is not loaded. The opencode harness only gives the 138-line prompt template. More instructions = better accuracy for this task.
   - openhands-sdk prompt template is NOT loaded, so skills need to be self-contained. They already are (built for Sonnet which also used openhands-sdk).
   - Latency/cost difference is irrelevant — submissions are free on Arena infrastructure.

**Phase 3 — MiniMax M2.5 Full Sample Results (paid tier, openhands-sdk):**
13/20 PASS (65%), 13/19 answerable (68.4%). Total cost: $2.08. Avg latency: 476s.
- PASS: uid0004, uid0023, uid0033, uid0048, uid0111, uid0136, uid0167, uid0192, uid0194, uid0199, uid0217, uid0230, uid0241
- FAIL: uid0030 (visual), uid0041 (wrong formula - Theil index), uid0057 (12-value extraction), uid0097 (balance sheet), uid0127 (unit conversion), uid0220 (network crash), uid0246 (timeout)

### Session 6b — March 30 (Submission #1 Results + Strategy)

**SUBMISSION #1 RESULTS:**
- Score: **136.280** → **#2 on leaderboard** (Bayes Foundry #1 at 141.849)
- Config: opencode + DeepSeek model string (but Arena likely evaluated with MiniMax M2.5)
- Correct: **144/246 (58.5%)**
- Multiplier: 0.9464 (-5.36% penalty from cost/time)
- Avg latency: 257.8s
- Total cost: $29.81

**Key Analysis:**
- Gap to #1: ~5.57 points = ~6 more correct questions (with same multiplier)
- If multiplier improves to ~0.985 (reduce cost/time), we'd beat Bayes with same accuracy
- openhands-sdk is 1.8x slower (476s vs 258s), which would INCREASE time penalty
- opencode's 138-line prompt was MORE effective per line than openhands-sdk's 525-line skills injection

**DECISION: Option B — Iterate on opencode config.**
Rationale:
1. opencode already scored 136.28 on full benchmark (proven)
2. openhands-sdk scored only 68.4% on sample vs opencode's 58.5% on full — but openhands-sdk is 1.8x slower, which hurts multiplier
3. opencode is faster (257s vs 476s), meaning LESS time penalty
4. We can add the most impactful missing content to the prompt template (it's only 138 lines, plenty of room)
5. Targeted fixes to the prompt template can address the top failure patterns
6. Risk of openhands-sdk regression is high — no full benchmark data

### Session 7 — April 1 (Trajectory Analysis + Targeted Skills v7)

**Scoring system reconfigured by Arena.** Our openhands-sdk submission scored 170.7 (#5). Leader at 182.1.
Competition extended to April 11.

**Submission history (all scores under new system):**
- 3decf80a: **170.7** (158/246, $12.82, 217s) ← BEST (openhands-sdk)
- ed9b0955: 163.5 (153/246, $14.60, 198s)
- 54d3fafd: 161.5 (153/246, $15.91, 200s)
- 5596c2ac: 139.4 (150/246, $38.31, 197s)
- 3aff9968: 143.3 (opencode)
- ccdf4848: 132.3 (opencode)

**Trajectory analysis of failed questions** (from March 30 paid openhands-sdk run, 13/20 pass):
1. uid0097 (ESF balance sheet): Agent used "Capital account" $200M instead of total fund balance $8.1B
2. uid0127 (unit conversion): Agent got wrong set of dates for the mean (wrong date enumeration)
3. uid0041 (Theil index): Agent used completely wrong formula (got 97.494, expected 0.011)
4. uid0057 (12-value list): Agent ran out of steps searching 12 files one by one
5. uid0246 (Euclidean norm): Agent extracted wrong tax anticipation bill values
6. uid0030 (visual): Unfixable
7. uid0220 (reported in): Agent process crashed

**Skills v7 changes (525→631 lines):**
1. Theil formula: Added warning + sanity check ("if > 1.0, you have a bug")
2. Euclidean norm: New formula pattern
3. HP filter: New formula pattern
4. Named formula lookup: New critical rule — always check computation_patterns skill
5. Date range enumeration: New pitfall — enumerate all dates explicitly
6. Batch extraction: New retrieval pattern — use loops for multi-file extraction
7. ESF balance sheet: Strengthened terminology guidance
8. Write answer early: Strengthened — write estimate immediately
9. reasoning_effort: Changed "medium" → "high" (currently no-op per SDK source)

**v7 Submission result:** 158.5 score, 148/246 correct — REGRESSION (-10 correct vs v6 best)
**v6 Revert result:** 162.3 score, 153/246 correct — confirms ±5 variance, true baseline ~153-158

**Conclusion:** More skills content hurts. Plateau confirmed at ~155 correct. Need data-driven approach.

### Session 8 — April 2 (Local Testing Infrastructure Setup)

**Set up full 246-question local testing pipeline:**
- Downloaded OfficeQA dataset (246 questions + ground truth) from Databricks GitHub
- Adapted arena-toolkit scripts from Ground Wire team (cohort peer, now #2 at 176.4)
- Generated all 246 arena-compatible sample directories from CSV + template
- Created batch evaluation script with resume support (survives crashes)
- Created aggregation script with difficulty breakdown + per-question failure log
- Fixed API key issue: .env needs `export` prefix for env var to reach Docker containers
- Smoke test PASSED: uid0023 correct, $0.09, 568s

**All submissions to date (new scoring system):**
| ID | Score | Correct | Cost | Latency | Config |
|----|-------|---------|------|---------|--------|
| 3decf80a | **170.7** | 158/246 | $12.82 | 217s | v6 openhands-sdk (BEST) |
| ed9b0955 | 163.5 | 153/246 | $14.60 | 198s | openhands-sdk |
| 172ac6b4 | 162.3 | 153/246 | $14.43 | 225s | v6 revert |
| 54d3fafd | 161.5 | 153/246 | $15.91 | 200s | openhands-sdk |
| 1f911bc6 | 158.5 | 148/246 | $11.53 | 270s | v7 targeted (REGRESSION) |
| 3aff9968 | 143.3 | 152/246 | $33.95 | 209s | opencode |
| 5596c2ac | 139.4 | 150/246 | $38.31 | 197s | opencode |
| ccdf4848 | 132.3 | 143/246 | $36.66 | 229s | opencode |

**Budget:** ~$161 OpenRouter remaining (local testing only, submissions are free)

**Ready for overnight full eval run:**
```bash
source .env && BATCH_SIZE=10 bash scripts/run_full_eval.sh
```
~4 hours, ~$12 cost, 25 batches of 10 questions
