# Solution Proposal — Dolores Research

**Team:** Leon (柳文浩), Dolores Research
**Date:** March 23, 2026

---

## Approach: Systematic Behavioral Engineering + Automated Skill Evolution

### The Thesis

The performance gap between baseline agents (~34-43%) and top performers (~68%) on OfficeQA is behavioral, not capability-based. The same model produces dramatically different results depending on the methodology it follows. We treat this as an engineering problem: discover failure modes, encode fixes as reusable skills, and validate that each skill improves accuracy without introducing regressions.

### Architecture

We use **OpenHands** as our agent harness, configured through Arena's standard pipeline:

1. **Prompt Template** — Encodes a four-phase methodology (Retrieve → Extract → Compute → Validate) that forces the agent to separate document retrieval from value extraction from computation. The critical constraint: *all arithmetic happens in Python, never in natural language*. This eliminates the cascading precision errors that account for a significant share of failures on analytical questions.

2. **Skills Library** — Domain-specific reference files the agent reads as context:
   - **Treasury Bulletin navigation** — table structure patterns, hierarchical header resolution, multi-page table handling, fiscal year vs calendar year conversion rules
   - **Computation patterns** — worked Python examples for every computation type in OfficeQA (linear regression, t-statistics, growth rates, multi-year aggregation)
   - **Known pitfalls** — a living catalog of failure patterns discovered through iteration, each with a concrete rule that prevents recurrence

3. **Self-Improvement Loop** — After each test run, we classify every failure (retrieval, parsing, computation, interpretation, visual), identify the highest-EV pattern to fix, encode the fix as a skill update, and verify no regressions. This is manual iteration at first, with the goal of automating it via EvoSkill.

### Research Direction: Automated Skill Discovery

We're exploring **EvoSkill** integration to automate the skill refinement loop. Rather than manually diagnosing each failure and writing skill updates, the evolution framework would:
- Analyze failed trajectories to identify recurring failure patterns
- Propose skill mutations (new rules, examples, or restructured instructions)
- Evaluate mutations against a held-out validation set
- Retain only improvements that pass a Pareto frontier check

This aligns with Sentient's research direction #1 (AI self-improvement/evolution). The question we're investigating: can automated skill evolution match or exceed carefully hand-crafted skills on a domain-specific benchmark like OfficeQA? And do the resulting skills transfer to other grounded reasoning tasks?

### Current Status

- Arena CLI installed, OpenHands harness configured, local testing operational
- Prompt template with four-phase pipeline deployed
- Three initial skills files authored from OfficeQA failure mode analysis
- First test runs completed — validating infrastructure and measuring per-question cost
- Iterating on sample questions to build failure catalog before first submission

### What Makes This Different

Most teams will optimize prompts. We're building a **skill engineering pipeline** — a systematic process for converting agent failures into reusable behavioral improvements. The prompt is scaffolding; the skills are the product. This mirrors how Dolores Research approaches AI orchestration more broadly: the model doesn't need to be smarter, it needs to follow the right methodology.

---

*Dolores Research — the performance gap is behavioral, not capability-based.*
