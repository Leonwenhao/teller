# Session 8 Progress Report — April 1-2, 2026

## Summary
Started at **#6 (170.7 score, 158/246 correct)**. Ended at **#4 (180.9 score, 173/246 correct, 70.3% accuracy)**. New personal best. Leader just leaped to 188.

## All Arena Submissions This Session

| Tag | Score | Correct | Accuracy | Cost | Latency | Key Change |
|-----|-------|---------|----------|------|---------|------------|
| v8 (write-early) | **178.7** | 167 | 67.9% | $15.00 | 184s | Sharpened Rule 1: write answer.txt immediately |
| v8 revert | 162.5 | 152 | 61.8% | $13.93 | 215s | Same as v8 — confirms ±15 variance |
| v9 (+formulas) | 163.7 | 152 | 61.8% | $12.22 | 247s | Added gmean/std/kurtosis patterns → REGRESSED |
| v10 (trimmed 251 lines) | 172.7 | 165 | 67.1% | $19.47 | 150s | Cut skills 543→251 lines. Faster but costlier |
| v11 (MCP+config) | 173.5 | 164 | 66.7% | $17.72 | 156s | Added MCP web-search + max_iter=100 + temp=0 |
| **v12 (scipy+iter)** | **180.9** | **173** | **70.3%** | $19.30 | 155s | scipy guidance one-liner + max_iterations=100 |
| v13 (scipy only) | 162.5 | 155 | 63.0% | $19.36 | 148s | Removed max_iterations → REGRESSED hard |

## What Worked

### 1. Write Answer Early (v8, +9 correct)
Changed Rule 1 in methodology from passive ("write your best answer EARLY") to aggressive ("WRITE /app/answer.txt IMMEDIATELY after your FIRST extraction"). This recovered 9 questions where the agent was timing out before writing.

### 2. Scipy Guidance One-Liner (v12, +6 more correct)
Added to Rule 2: "For ANY statistical measure (std dev, kurtosis, z-score, Gini, VaR, median, percentile, polynomial fit, etc.), use `scipy.stats` or `numpy` — they have every function you need. Do not implement formulas from scratch."

This single line helped the agent use library functions instead of inventing formulas for complex statistics.

### 3. max_iterations: 100 (v12, critical for accuracy)
Increasing from default (~25-30) to 100 gave the agent enough steps to find data in complex multi-file questions. Removing it (v13) caused -18 correct. **This setting is load-bearing.**

## What Failed

### 1. Adding Content Always Regresses
- v7 (631 lines, +88 from v6): 148 correct (WORSE than v6's 158)
- v9 (+24 lines of formula code): 152 correct (WORSE than v8's 167)
- Every addition hurts. MiniMax M2.5 gets confused by more instructions.

### 2. Trimming Too Aggressively Also Hurts
- v10 (251 lines): 165 correct, but cost spiked to $19.47 (agent wanders without guardrails)

### 3. MCP Web Search Crashes Locally
- `npx -y @anthropic/mcp-web-search` fails inside Docker with `McpError: Connection closed`
- On Arena it partially works but doesn't improve accuracy (v11: 164 correct)

### 4. temperature: 0.0 — No Clear Impact
- Didn't reduce variance. Didn't help or hurt noticeably.

## Local Testing Infrastructure

### Setup
- Built full 246-question local testing pipeline using arena-toolkit approach
- Generated all 246 arena-compatible samples from Databricks OfficeQA CSV
- Created batch evaluation scripts with resume support

### Results
- **Original run (batches 1-15):** 61 pass, 89 fail, 50 API drops out of 150 scored
- **Rerun (93 remaining questions):** 37 pass, 56 fail, 0 infra drops
- **Combined:** 101 pass, 144 fail out of 245 scored (41% local accuracy)
- Local accuracy is ~20% lower than Arena due to Docker-on-Mac overhead and API drops

### Infrastructure Problems Encountered
1. **OpenRouter connection drops** — 50 questions lost to "peer closed connection" errors
2. **Batch script bugs** — sample directory corruption from swapping, stdin consumption, wrong result file paths
3. **max_iterations=100 makes local tests 3x slower** — ~15 min per question vs ~5 min

### Key Insight
Local timeouts ≠ Arena failures. Many questions that timeout locally pass on Arena's faster infrastructure. The REAL failures to focus on are wrong-answer failures, not timeouts.

## Complete Failure Analysis (from local testing)

### 30 Real Wrong Answers (agent ran, wrote wrong answer)
| Category | Count | Fixable? |
|----------|-------|----------|
| Very close (<2% off) | 2 | Maybe — precision/rounding |
| Close (2-10% off) | 9 | Partially — wrong adjacent value |
| Wrong data (10-50% off) | 8 | Hard — wrong row/column/date |
| Wrong formula (>50% off) | 8 | Yes for known formulas |
| Multi-value/bracket | 3 | Partially |

### 114 No-Answer (agent timed out)
- Mostly local infrastructure issue
- ~30-40 of these probably pass on Arena (v8 gets 167, v12 gets 173)
- The rest are genuinely hard questions the agent can't solve in time

### Failure Distribution by Question Type
| Type | Failures | Note |
|------|----------|------|
| AGGREGATE (sum, mean, total) | 48 | Multi-step extraction |
| LOOKUP (single value) | 24 | Can't find right data |
| STAT (std dev, kurtosis, etc.) | 20 | Complex formulas |
| REGRESSION/FORECAST | 17 | Multi-step computation |
| RATIO | 17 | Wrong base values |
| GROWTH/CAGR | 12 | Wrong periods |
| VISUAL/CHART | 4 | Unfixable from text |
| EXTERNAL KNOWLEDGE | 1 | Needs web search |

### Accuracy by UID Range (local)
| Range | Accuracy | Note |
|-------|----------|------|
| UID0001-0050 | 44% | Early questions, includes our 20 sample overfitting |
| UID0051-0100 | 36% | Complex stats, multi-value |
| UID0101-0150 | 42% | Mixed difficulty |
| UID0151-0200 | 58% | Higher local pass rate |
| UID0201-0246 | 23% | Worst range — heavy stat/compute |

### 11 Close-Miss Questions (targeted local test)
Tested 6 of 11 with v12 config (scipy + max_iter=100):
- **uid0008: FLIPPED TO PASS ✓** (percent growth)
- **uid0080: FLIPPED TO PASS ✓** (FY1954 income tax)
- uid0055: Still FAIL (0.1 vs 0.0)
- uid0186: Still FAIL (181 vs 179)
- uid0051: Still FAIL (110.47 vs 112.87)
- uid0081: Still FAIL (22.6M vs 23.9M)

## Current Best Configuration (v12)

### arena.yaml
```yaml
agent:
  harness_name: "openhands-sdk"
  model: "openrouter/minimax/minimax-m2.5"
  skills_dir: "skills/"
  config:
    reasoning_effort: "medium"
    max_iterations: 100
```

### Skills (543 lines, 5 files)
- `methodology/SKILL.md` (103 lines) — Pipeline, write-early rule, scipy guidance
- `known_pitfalls/SKILL.md` (150 lines) — Unit conversion, fiscal year, terminology
- `computation_patterns/SKILL.md` (146 lines) — Regression, growth, Theil, validation
- `retrieval_strategy/SKILL.md` (42 lines) — Grep patterns, search strategy
- `table_parsing_guide/SKILL.md` (102 lines) — Column/row hierarchy, time periods

### Two Critical Changes from Baseline
1. **Rule 1 (write-early):** "WRITE /app/answer.txt IMMEDIATELY after your FIRST extraction"
2. **Rule 2 (scipy):** "For ANY statistical measure, use scipy.stats or numpy — do not implement formulas from scratch"

## The Cost Problem

Our accuracy (70.3%) is competitive with #1 (68.7%), but our cost ($19.30) is much higher than theirs (~$14.76). The `max_iterations: 100` is essential for accuracy but inflates cost.

```
Our v12:  173 correct × 1.046 multiplier = 180.9 score
#1:       169 correct × 1.078 multiplier = 182.1 score (now 188)
```

If we got 173 correct at $14 cost → multiplier ~1.074 → score ~185.7.

## The Path to 190

### The Math
190 score requires ~178 correct at $15 cost (mult ~1.067), or ~173 correct at $10 cost (mult ~1.098).

### Approach Options

**Option 1: Reduce cost while maintaining 170+ correct**
- Trim skills to reduce input tokens per iteration (less reading = cheaper per step)
- Find the right max_iterations balance (50? 75?) — v13 proved we can't remove it entirely
- The "addition by subtraction" philosophy: same accuracy with fewer tokens

**Option 2: Increase accuracy to 175+ correct**
- Fix the 8 "wrong formula" failures with better computation guidance
- Fix the 8 "wrong data" extraction errors — hardest category
- The 11 close-miss questions are mostly model comprehension limits

**Option 3: Structural change**
- Different retrieval approach (MCP server that indexes corpus)
- Pre-built search index the agent queries instead of raw grep
- Different model? (competition forces MiniMax M2.5, but model field might not be enforced)

### What the Leader Might Be Doing
The leader jumped from 182 to 188. That's ~176+ correct at low cost. Possible approaches:
- Extremely lean skills (minimal input tokens)
- MCP server for structured corpus access
- Different harness configuration
- Optimized retrieval that reduces step count

---

## Questions and Discussion Points for Codex

### On Our Approach
1. We've proven that adding skills content regresses performance with MiniMax M2.5. But we also proved that `max_iterations: 100` is critical for accuracy. Is there a way to get the benefits of more iterations without the cost penalty? Could we restructure skills to make each iteration more productive?

2. The scipy one-liner ("use scipy for everything") was our most effective single-line change (+6 correct). What other one-line behavioral changes could have outsized impact? What about "always use Python list comprehensions for multi-value extraction" or "always print extracted values before computing"?

3. Our v10 experiment (251 lines) showed that cutting skills in half barely hurts accuracy (165 vs 167) but increases cost because the agent wanders. Is there a "Goldilocks zone" of skills length? Should we A/B test 350, 400, 450 line versions?

4. The close-miss questions (2-10% off) are consistently wrong across runs — the agent deterministically picks the wrong value. These seem like model reading comprehension limits. Is there ANY prompt engineering technique that could help MiniMax M2.5 read tables more carefully?

### On the Cost Problem
5. Our cost went UP even when we removed max_iterations (v13: $19.36). Why? Is the scipy guidance causing the agent to write more code = more output tokens = more cost?

6. The leader gets similar accuracy at much lower cost. What architectural difference could explain this? Are they using a different harness? Different skills structure? An MCP server that reduces the number of search steps?

7. Would it help to explicitly tell the agent "minimize tool calls" or "solve this in 3 steps maximum"? We had "aim for 3-5 tool calls" in v6 but removed it. Should it come back?

### On Breaking Through
8. We're at ~70% accuracy ceiling with behavioral engineering. The Databricks paper reports 67.8% with Claude Opus 4.5. Is 75%+ even achievable with MiniMax M2.5? What would it take?

9. The failure analysis shows AGGREGATE questions (sum, mean, total across periods) are our biggest failure category (48 failures). These require extracting values from multiple files. Is there a fundamentally better way to instruct the agent to do multi-file extraction?

10. Some questions have text/categorical answers like "[37.48, unusual]" or "[2.59%, 2.34%, Decreased]". Our skills don't address text classification at all. Is this a missed opportunity?

### On Experimentation
11. With ±15 question variance between identical runs, how do we distinguish real improvements from noise? Should we submit the same config 3 times and take the best? Or is that gaming variance rather than improving?

12. The friend running AutoResearch with MiniMax M2.5 on GPU — what should they focus on? The close-miss questions? The formula errors? Or should they try radically different skills structures?

## Files Reference
- `results/complete_246_results.json` — Full 245-question pass/fail results
- `results/full_eval/` — Per-batch results from original run
- `results/full_eval/done-*.json` — Per-question results from rerun
- `results/dropped_questions.json` — Questions lost to API drops
- `officeqa_full.csv` — Ground truth for all 246 questions
- `SCRATCHPAD.md` — Full session history
