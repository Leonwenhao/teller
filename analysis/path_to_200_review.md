# Path to 200 — Strategic Review
**Date:** March 30, 2026
**Current score:** 136.28 (#2, 144/246 correct, 0.9464 multiplier)
**Leader:** Bayes Foundry 141.85

---

## 1. Strategy Audit

### Lever 1: Mega Prompt Template — AGREE with modifications

**Assessment: High-value, moderate risk. Recommend 250-300 lines, not 400-500.**

The core insight is correct: opencode copies skills to `~/.config/opencode/skills/` but does NOT inject them into the agent's context. Our 525 lines of skills are invisible to MiniMax during execution. The agent only sees the 148-line prompt template + the question + resource boilerplate that Arena appends.

However, the impact estimate of +15-25 correct is likely too optimistic. Here's why:
- The prompt template already covers the HIGHEST-value content from skills (unit conversion, reported-in rule, financial terminology, computation patterns, output formatting, web search, known pitfalls)
- What's missing is depth, not breadth: detailed examples, edge cases, OCR artifacts, table parsing mechanics
- Adding 350+ lines of additional context risks **attention dilution** — MiniMax M2.5 has to process all this before even reading the question. With 196K context, length isn't the issue; cognitive focus is.

**Recommended approach:** Selective merge to ~250-300 lines. Prioritize content that addresses the most common failure patterns on the 102 failed questions. Don't include generic advice or validation patterns that don't add information density.

### Lever 2: Full 246-Question Local Run — STRONGLY AGREE

**Assessment: Highest diagnostic value per dollar. Do this FIRST.**

Without per-question results from Arena, we're flying blind. We know 102 questions failed but not which ones or why. A local run costs ~$5 with MiniMax ($0.02/q × 246) and gives us:
- Per-question pass/fail for all 246
- Failure categorization (retrieval, parsing, computation, interpretation, timeout, infra)
- Direct comparison of local vs Arena results on the 20 sample overlap
- Data to prioritize prompt template improvements by expected value

**Caveat:** We can't run all 246 locally because we only have 20 sample tasks. To test all 246, we'd need Arena's full task set — which we don't have access to locally. The real value here is **submitting more times to Arena** (3/day, free) with targeted changes and tracking which changes improve the score.

### Lever 3: Multiplier Optimization — AGREE but secondary

**Assessment: Worth 5-15 points, but accuracy gains are more impactful.**

The math:
- Current: 144 correct × 0.9464 = 136.28
- If multiplier hits 1.00: 144 × 1.0 = 144.0 (+7.7 points)
- If multiplier hits 1.05: 144 × 1.05 = 151.2 (+14.9 points)
- If multiplier hits 1.15 (max): 144 × 1.15 = 165.6 (+29.3 points)

But getting +10 correct answers (to 154) even with the same penalty: 154 × 0.9464 = 145.7 (+9.4 points). So accuracy and multiplier have comparable point values, but accuracy is more reliable — we know exactly what to fix.

The v2 "Be FAST" rule is a good start. The key lever is reducing tool calls per question (opencode used 5 tool calls for uid0023 vs openhands-sdk's 27 actions). opencode is inherently faster.

---

## 2. The openhands-sdk Paradox — Investigation Findings

### Sample difficulty distribution
- Sample: 10 easy, 10 hard (50% hard)
- Full benchmark: 113 easy, 133 hard (54.1% hard)
- The sample is NOT disproportionately hard. It's slightly easier than the full benchmark.

### Why openhands-sdk (68.4%) didn't dramatically outperform opencode (58.5%)

The paradox: openhands-sdk injects 525 lines of skills into the system prompt, yet scored comparably to opencode which only delivers 148 lines. Multiple factors explain this:

**Factor 1: openhands-sdk is dramatically slower (1.8x).**
- opencode uid0023: 160s, 5 tool calls
- openhands-sdk uid0023: 229s, 27+ actions
- openhands-sdk's higher action count means more inference calls, more cost, more latency. On the 900s timeout, this means fewer complex questions complete successfully.

**Factor 2: Different tool interfaces.**
opencode gives MiniMax native tools (grep, read, bash) as structured tool calls. openhands-sdk runs through OpenHands' action framework (CmdRunAction, IPythonRunCellAction) with more overhead per step. The tool calling format matters — MiniMax M2.5 scored 76.8 on BFCL (function calling benchmark), meaning it's optimized for structured tool calls, which opencode provides more directly.

**Factor 3: Prompt template quality > quantity.**
The 148-line prompt template is highly curated — every line addresses a specific failure mode. The 525 lines of skills include general reference material, verbose examples, and content the model may already know (like how to use grep). More context doesn't always help; focused, high-signal context does.

**Factor 4: The comparison isn't apples-to-apples.**
- openhands-sdk: 13/19 on sample (local, our API key, Docker on Mac)
- opencode: 144/246 on full benchmark (Arena infra, Arena API key, different hardware)
- Network conditions, rate limits, hardware all differ

### Conclusion
opencode is the better harness for MiniMax M2.5, not despite having less content, but partly because of it. The key optimization path is making the prompt template more effective, not switching to openhands-sdk.

---

## 3. Prompt Merge Recommendation

### Content already in prompt template (keep as-is)
- Critical rules (answer.txt, Python-only, grep-first, no planning, be fast) — 8 lines
- Unit conversion rules — 7 lines
- "Reported in" date rule — 4 lines
- Financial statement terminology — 5 lines
- Four-phase methodology — 30 lines
- Computation patterns (linregress, growth rate, CAGR, average, Theil, ttest) — 30 lines
- Output format rules — 16 lines
- Web search capability — 14 lines
- Known pitfalls — 8 lines

### Content in skills NOT in prompt — prioritized for merging

**HIGH PRIORITY (add to prompt):**

1. **Detailed unit conversion with worked example** (known_pitfalls lines 19-25): The `raw_table_value * 1000` code example is concrete and actionable. The prompt has the rule but not the worked example. ~7 lines.

2. **Unit indicator locations** (known_pitfalls lines 32-43): "Unit indicator can appear in four places: table title, header row, column header, footnote." The prompt says "check table title" but this expanded list catches more cases. ~5 lines condensed.

3. **Document versioning — mechanistic instructions** (known_pitfalls lines 56-68): The prompt has a one-liner about later bulletins. The skill has specific grep commands. ~6 lines condensed.

4. **OCR artifacts** (known_pitfalls lines 78-89): Pre-1996 documents have L/1, O/0 confusion, comma/decimal errors. Not in prompt at all. ~4 lines condensed.

5. **Common false cognates** (known_pitfalls lines 99-108): "Receipts" in revenue vs securities, "Expenditures" vs "Outlays." The prompt mentions receipts but not the full list. ~4 lines.

6. **"Reported in" vs "Reported for" — forceful version** (known_pitfalls lines 110-120): The prompt has the rule but the skill has "STOP AND READ THIS CAREFULLY" with three explicit rules. More forceful = better compliance. Replace current 4-line version with ~8-line version.

7. **Calendar year from monthly data** (computation_patterns lines 97-111): How to construct calendar year totals from fiscal year monthly data. Not in prompt. ~6 lines condensed.

8. **Markdown table column paths** (table_parsing lines 79-88): "Hierarchy is flattened into dash-separated paths." This is essential for parsing the actual corpus format. ~4 lines.

**MEDIUM PRIORITY (consider adding):**

9. **Retrieval fallback strategies** (retrieval_strategy lines 31-36): "Try synonyms, next month's bulletin, table of contents, broader search." ~4 lines.

10. **Step budget awareness** (retrieval_strategy lines 37-41): "Don't spend more than 15 steps on retrieval." Reinforces the "be fast" rule. ~2 lines.

11. **Multi-page table awareness** (table_parsing lines 58-65): Tables span pages, headers repeat. ~3 lines.

**LOW PRIORITY (omit):**
- Table anatomy basics (table_parsing lines 12-19) — the model already knows this
- Hierarchical header examples with ASCII art (table_parsing lines 22-56) — too verbose, minimal ROI
- Validation function code (computation_patterns lines 113-133) — conflicts with "be fast"
- Full growth rate function definitions (computation_patterns lines 43-61) — already have one-liner
- Pattern 4/5 (ratio, multi-year summation) — trivial, model knows these

### Recommended merge: add ~50-55 lines to prompt template

Target: 200-210 lines total. This keeps the prompt focused while covering the critical gaps. The additions should be integrated into existing sections, not appended as new sections.

### Redundancy to eliminate
- The prompt has unit conversion in BOTH the dedicated section (lines 10-16) AND in the compute phase (lines 51-56). Consolidate.
- Output format rules appear in BOTH Phase 4 validation (line 101) AND the Output Format section (lines 103-118). The Phase 4 mention can be trimmed.
- "Write ONLY the bare number" appears on line 101 AND line 111. Remove one.

---

## 4. Alternative Approaches

### MCP Servers — Worth investigating
The README shows MCP server support for all harnesses. A web search MCP server (`@anthropic/mcp-web-search`) could replace our manual Wikipedia API lookup, potentially being more reliable and faster. A filesystem MCP server could provide better file reading tools.

However: MCP servers add setup overhead and potential failure points. The risk/reward is questionable for +1-2 correct answers.

### reasoning_effort config
The README shows `config: reasoning_effort: "high"` as an option for opencode. We're not setting this. Worth testing whether `reasoning_effort: "low"` speeds up execution (improving multiplier) while `"high"` improves accuracy on hard questions. This is a free parameter we haven't explored.

### Running both configs on Arena
We have 3 submissions/day. Submitting BOTH opencode and openhands-sdk configs gives us direct Arena comparison data. Even if openhands-sdk scores lower, the per-config-delta tells us exactly how much skills injection is worth. This is highly informative for ~0 cost.

### Alternative harnesses
The README lists `goose` and `codex` as additional harnesses. We haven't tested either. `goose` supports the same providers as opencode and might handle MiniMax differently. `codex` requires OpenAI models so it's not relevant. Worth a quick goose test.

### Per-question Arena results
We checked — Arena CLI only provides aggregate results (total correct, score, latency, cost). No per-question breakdown. The `arena compare` command listed in README doesn't exist in the current CLI version. The only way to get per-question data is local testing.

### MiniMax thinking control
MiniMax M2.5 has a known "thinking overhead" issue (GitHub issue #77). The thinking process adds latency without always improving accuracy. We can't directly control this through the harness, but we CAN influence it indirectly:
- Simpler, more direct prompt instructions reduce thinking time
- "Be FAST. Aim for 3-5 tool calls." signals the model to think less
- `reasoning_effort: "low"` might control this (untested)

---

## 5. Recommended Path to 200 — Concrete Steps

### Priority 1: Submit and iterate (Days 1-2)
Use all 3 daily submissions for maximum data:

1. **Submission A (already submitted):** opencode v2 with speed + formula fixes (pending)
2. **Submission B (tomorrow):** opencode v3 with mega prompt (~200-210 lines, selective skills merge)
3. **Submission C (tomorrow):** openhands-sdk config for Arena baseline comparison

Each submission gives 144+ data points. Compare scores to isolate which changes help.

### Priority 2: Build the mega prompt (tonight/tomorrow morning)
Merge the ~50-55 high-priority lines identified above into the prompt template. Key additions:
- Worked unit conversion example with code
- Unit indicator locations (four places to check)
- OCR artifact awareness
- Calendar year from monthly data pattern
- Markdown column path format
- Stronger "reported in" rule
- Retrieval fallback strategies

Eliminate redundancy. Target 200-210 lines.

### Priority 3: Test reasoning_effort parameter
Run uid0023 and uid0041 locally with:
```yaml
config:
  reasoning_effort: "low"   # test this
```
vs the default. If "low" reduces latency significantly without hurting easy questions, it could flip the multiplier penalty to a bonus (+10-15 points for free).

### Priority 4: Test goose harness
Quick compatibility test. If goose handles skills differently than opencode, it could be an alternative path. 1 local test, $0.02.

### Priority 5: Failure pattern analysis from submission results
When v2 results come in, compare: did the score improve? By how much? This tells us whether speed optimizations or formula additions had more impact. Use this to calibrate the next round.

### Score projection
- Mega prompt (+10-15 correct from skills content reaching the model)
- Multiplier optimization (+5-10 equivalent points from speed/cost improvement)
- Formula/pattern fixes (+3-5 correct from specialized stats, edge cases)
- Net: 154-164 correct × 1.0-1.05 multiplier = **154-172 points**

To reach 200, we'd need ~175 correct with a 1.14 multiplier, or ~190 correct with a 1.05 multiplier. This requires 76-77% accuracy — a significant jump from 58.5%. The most credible path is through the mega prompt (getting skills content to the model) + systematic failure analysis + multiplier optimization. 200 is ambitious but achievable if the skills content is as impactful as Sonnet's 94.7% sample score suggests.

### The key bet
The fundamental question is: **how much of Sonnet's 94.7% sample accuracy came from the skills content vs Sonnet's superior reasoning?** If skills content accounts for even half the gap (from ~58% to ~78%), the mega prompt could get us to 170+. If it's mostly Sonnet's reasoning, the mega prompt only gets us to 150-155.

We'll know after submission B (mega prompt) comes back.
