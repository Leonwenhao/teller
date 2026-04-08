# Dolores Research — Sentient Arena Cohort 0 Report

## 1. Team Info

- **Team name:** Dolores Research
- **Team members:** Leon Liu (柳文浩), solo participant

## 2. What We Built

**Idea:** The performance gap on enterprise document reasoning is behavioral, not capability-based. Rather than changing the model, we engineered *how* the agent approaches Treasury Bulletin questions through targeted domain knowledge and harness architecture selection.

**Approach:** An 84-line prompt template delivered through the Goose harness, containing three behavioral rules, 20+ named statistical formulas, unit conversion rules, fiscal year conventions, Treasury-specific terminology traps, embedded CPI reference data, and a multi-file retrieval strategy. No custom code, no pre-built pipelines — pure prompt engineering and harness optimization.

**What made it work:**
- **Prompt density over volume.** MiniMax M2.5 (10B active params, MoE) is sensitive to attention dilution. An 84-line prompt with zero tutorials outperformed a 543-line version with detailed code examples. Every line is a rule, formula, trap, or data point.
- **Harness architecture.** Switching from OpenHands SDK to Goose gave us auto-compaction (context window management that prevents accuracy degradation on multi-step questions) and an 87% cost reduction ($1.85 vs $14.50 per run).
- **Three critical rules:** (1) Write answer.txt in every Python block (insurance against empty files — removing this lost 22 answers). (2) All math in Python/scipy (prevents precision errors). (3) Stop immediately after writing final answer (prevents self-sabotage overwrites).

**Best result:** 192.046 score, 174/246 correct (70.7%), $1.85 total cost, 171s avg latency.

## 3. How We Worked On It

**Process:** 12 optimization sessions over 14 days, 25+ Arena submissions.

- **Failure analysis driven.** After each submission, we pulled traces and classified failures into retrieval (wrong file), extraction (wrong cell), computation (wrong formula), and behavioral (empty answer, self-sabotage). Fixes targeted the highest-EV failure category.
- **Cross-submission variance analysis.** We compared pass/fail results across 6 submissions to identify 114 always-pass questions (reliable base), 43 always-fail questions (structural gaps), and 89 swing questions (variance-driven). The always-fail analysis revealed specific missing formulas and reference data, which we added.
- **Prompt iteration.** We tested 8+ prompt versions from 37 lines to 631 lines. More content consistently regressed. We learned that MiniMax M2.5 needs *rules and data*, not *tutorials and examples*.
- **Harness evaluation.** We tested OpenCode, OpenHands SDK, and Goose. The Goose discovery was the single biggest performance breakthrough — context auto-compaction solved a documented accuracy degradation (80% early → 60% late) that no prompt change could fix.
- **Multi-agent research.** We used Claude, ChatGPT, and Gemini for parallel deep research on MiniMax optimization, OfficeQA patterns, and competitor analysis. Findings were synthesized and tested empirically.

## 4. What We Found

**Patterns in OfficeQA:**
- Unit conversion is the #1 error pattern. Treasury tables say "in thousands" in four different places (title, header row, column header, footnotes). Questions ask for "nominal dollars." Missing the conversion = instant wrong answer.
- Fiscal year confusion (pre-1976: Jul–Jun; post-1976: Oct–Sep) is the #2 error pattern.
- "Reported IN February 1938" vs "reported FOR February 1938" changes which file you must open. This distinction determines retrieval correctness.
- ~6 questions require visual chart reading (unfixable with text-only agents). ~10 require external data not in the corpus.

**Tricks that helped:**
- Embedding CPI-U annual averages directly in the prompt (publicly available BLS data) so the agent can do inflation adjustments without web search.
- "Retrospective table first" strategy for multi-year questions — a single later bulletin often has a historical summary table that replaces searching 12 individual files.
- The "write answer in every Python block" insurance policy was worth ~22 correct answers alone.

**Surprising findings:**
- Prompt length has an inverse relationship with accuracy on MiniMax M2.5. Our 84-line prompt outscored our 543-line prompt by 6+ points despite containing less information.
- The agent harness affected accuracy more than any prompt change. Switching from OpenHands SDK to Goose added ~5 correct answers with zero prompt modifications.
- Infrastructure load significantly impacts scores. Our best submission was at 2 AM on empty infrastructure (171s latency). Daytime submissions on congested infrastructure averaged 200s+ latency and 6+ fewer correct answers.

**Things that didn't work:**
- Adding more detailed code examples (model already knows scipy/numpy — #1 in tool calling)
- Consolidating 5 skills files into 1 (ordering/structure matters)
- Applying software engineering principles (DRY, no contradictions) to prompts — the "contradictions" were actually load-bearing insurance policies
- Context condenser via OpenHands SDK config (not wirable through arena.yaml)
- max_message_chars truncation (caused agent to re-read files, increasing cost)

## 5. Feedback for Arena

**What was confusing:**
- The skills injection bug was the biggest source of confusion. We spent days optimizing skills content that may not have been reaching the agent in production. Knowing earlier would have saved significant iteration time.
- The scoring formula was never officially published. We reverse-engineered it from submission data, but uncertainty about the exact coefficients made cost/latency optimization harder than necessary.

**Things we wish worked:**
- Context condensation configurable through arena.yaml for OpenHands SDK. This is the #1 performance bottleneck for multi-step agent tasks.
- A way to see per-question results (not just aggregate score) without parsing traces. This would dramatically accelerate the failure analysis loop.
- Local testing with the same infrastructure conditions as production. Our local runs took 16 min/question vs 3 min on Arena, making local iteration impractical.

**Improvements for future cohorts:**
- Publish the scoring formula explicitly so teams can optimize intentionally rather than through reverse engineering.
- Provide a dedicated test queue with guaranteed infrastructure isolation, separate from the production evaluation queue.
- Standardize harness capabilities — the fact that Goose, OpenHands SDK, and OpenCode have fundamentally different context management, skills injection, and cost profiles makes the competition partially about harness discovery rather than agent engineering.
- Surface per-question pass/fail in the results API to enable systematic failure analysis.

**What would have helped us move faster:**
- Earlier visibility into the skills injection bug. A simple "skills loaded: yes/no" in the trace output would have caught this immediately.
- More than 5 submissions per day. The 3-hour turnaround per submission means each day only allows 2-3 experimental iterations with results-informed decisions.
- A public channel for sharing harness compatibility findings (which harnesses support which features) would benefit all participants.
