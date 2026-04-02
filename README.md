# Sentient Arena — Grounded Reasoning Agent

**Team:** Dolores Research  
**Competition:** Sentient Arena Cohort 0 — Grounded Reasoning  
**Benchmark:** OfficeQA by Databricks (246 questions, 89K pages of U.S. Treasury Bulletins)  
**Current Best:** 170.7 score, 158/246 correct (64.2%)  
**Target:** 190+ score, 175+ correct (71%+)

## Quick Start

```bash
# 1. Install Arena CLI
curl -fsSL https://install.arena.sentient.xyz | bash
arena auth login

# 2. Configure
cp .env.example .env
# Edit .env with your OpenRouter API key (must have 'export' prefix)

# 3. Generate all 246 test questions
arena pull                              # Get template samples
python3 scripts/generate_samples.py     # Generate all 246
python3 scripts/verify_samples.py       # Verify scoring

# 4. Run evaluation
source .env && arena test --all --tag my-test

# 5. Submit to Arena (free, uses their API keys)
source .env && arena submit --tag my-submission
```

## Architecture

```
                    ┌─────────────────────┐
                    │   MiniMax M2.5      │  ← Model (fixed by Arena)
                    │   via OpenHands SDK │  ← Harness (fixed)
                    └──────┬──────────────┘
                           │ reads
                    ┌──────▼──────────────┐
                    │   Skills (5 files)   │  ← WHAT WE OPTIMIZE
                    │   ~543 lines total   │
                    └──────┬──────────────┘
                           │ guides
                    ┌──────▼──────────────┐
                    │   Agent Execution    │
                    │   grep → extract →  │
                    │   compute → answer  │
                    └──────┬──────────────┘
                           │ searches
                    ┌──────▼──────────────┐
                    │   697 Treasury      │
                    │   Bulletin TXT files │
                    └─────────────────────┘
```

**We can only change the skills files.** Everything else is fixed by the competition.

## Repository Structure

```
├── arena.yaml              # Agent config (harness + model + skills)
├── program.md              # AutoResearch-style self-improvement instructions
├── officeqa_full.csv        # All 246 questions with ground truth
├── skills/                  # ← THE OPTIMIZATION TARGET
│   ├── methodology/SKILL.md         # Execution pipeline (104 lines)
│   ├── known_pitfalls/SKILL.md      # Error prevention (150 lines)
│   ├── computation_patterns/SKILL.md # Python formulas (146 lines)
│   ├── retrieval_strategy/SKILL.md  # Document search (42 lines)
│   └── table_parsing_guide/SKILL.md # Table navigation (102 lines)
├── scripts/
│   ├── generate_samples.py  # Generate arena-compatible samples for all 246 Qs
│   ├── run_full_eval.sh     # Batch evaluation with resume support
│   ├── aggregate_results.py # Results analysis with failure breakdown
│   └── verify_samples.py    # Verify scoring pipeline
├── prompts/
│   └── officeqa_prompt.j2   # Prompt template (unused by openhands-sdk)
├── results/                 # Evaluation results (gitignored)
├── .env.example             # API key template
└── SCRATCHPAD.md            # Session state and decision log
```

## How Scoring Works

```
Arena Score = correct_questions × multiplier
multiplier ≈ 1.19 - 0.0056 × total_cost($) - 0.00028 × avg_latency(s)
```

- Each correct answer ≈ +1 point
- Each $1 of cost ≈ -0.9 points  
- Accuracy is the dominant factor

Questions are scored with **1% fuzzy numeric tolerance** — if your answer is within 1% of ground truth, it passes.

## The Benchmark: OfficeQA

[OfficeQA](https://github.com/databricks/officeqa) has 246 questions (113 easy, 133 hard):
- Document retrieval from a 697-file corpus of U.S. Treasury Bulletins (1939-2025)
- Table parsing with hierarchical headers
- Unit conversion (thousands/millions/billions)
- Fiscal year vs calendar year handling
- Statistical computation (regression, Theil index, HP filter, t-tests)
- External knowledge (historical country groupings, economic definitions)
- ~7 questions reference charts (unfixable from text-only corpus)

Best published accuracy: ~67.8% (Claude Opus 4.5 with pre-parsed docs).

## Competition Rules

- **Everyone uses MiniMax M2.5** — model field in arena.yaml is ignored
- **Submissions are free** — Arena uses their API keys
- **3 submissions per day** (resets midnight UTC)
- Competition is purely **behavioral engineering**: skills + prompt design
- Deadline: April 11, 2026

## Self-Improvement Loop

See `program.md` for autonomous experimentation instructions (compatible with [Karpathy's AutoResearch](https://github.com/karpathy/autoresearch) pattern).

The loop: **modify skills → evaluate → keep if improved, revert if not → repeat.**

Key insight: **more instructions ≠ more accuracy.** We've proven this twice. The agent (MiniMax M2.5) gets confused by verbose instructions. Keep skills concise and precise.

## Key Findings

| Config | Correct | Score | Insight |
|--------|---------|-------|---------|
| v6 skills (543 lines) | 153-158 | 162-170 | **Best performing** |
| v7 skills (631 lines) | 148 | 158 | More lines = regression |
| opencode harness | 143-152 | 132-143 | openhands-sdk is better |
| ±5 question variance | — | — | Same config, different results per run |

## License

Private repository. Dolores Research, 2026.
