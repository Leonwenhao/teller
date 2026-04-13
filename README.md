# Teller

<p align="center">
  <img src="assets/teller-mascot.png" alt="Teller mascot" width="400">
</p>

**An open-source grounded reasoning agent for enterprise document QA.**

Built by [Dolores Research](https://doloresresearch.com). Validated on the [OfficeQA benchmark](https://github.com/databricks/officeqa) by Databricks.

| Metric | Result |
|--------|--------|
| **Accuracy** | 71.5% (176/246) on OfficeQA — highest in the competition |
| **Rank** | #1 on [Sentient Arena](https://arena.sentient.xyz) Cohort 0 leaderboard |
| **Score** | 187.823 (peak: 192.046) |
| **Cost** | $1.85 total ($0.0075/question) |
| **Model** | MiniMax M2.5 (10B active params) |
| **vs. Claude Opus 4.5** | +3.7% accuracy at 1/500th the cost |

> The performance gap on enterprise document reasoning is behavioral, not capability-based. A 10B-parameter model, properly orchestrated, outperforms models 20x its size.

## What This Agent Does

Teller is a **document-to-answer system** — it retrieves, extracts, computes, and validates answers from large document archives in a single pipeline:

```
  Question (natural language)
         │
         ▼
  ┌─────────────────┐
  │  1. RETRIEVE     │  grep corpus → locate relevant files
  │  2. EXTRACT      │  parse tables → trace column hierarchies → get raw values
  │  3. COMPUTE      │  Python/scipy → 20+ statistical formulas → precise results
  │  4. VALIDATE     │  unit check → fiscal year → plausibility → write answer
  └─────────────────┘
         │
         ▼
  Answer (bare number, 1% tolerance)
```

**No existing product does all four steps.** Document search tools (Elastic, AlphaSense) find documents but don't compute. Parsing tools (Textract, Unstructured.io) extract data but don't reason. Analytics tools (Python, Excel) compute but require manual data entry. Teller goes from raw documents to validated numerical answers.

## Quick Start

### 1. Install Goose

[Goose](https://github.com/block/goose) is the open-source AI agent framework by Block Inc. that powers the runtime.

```bash
# macOS/Linux
brew install block-goose-cli

# or via install script
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash
```

### 2. Configure

```bash
git clone https://github.com/Leonwenhao/teller.git
cd teller

# Set your OpenRouter API key
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY=sk-or-v1-...

# Configure goose to use OpenRouter
export GOOSE_PROVIDER="openrouter"
export GOOSE_MODEL="minimax/minimax-m2.5"
source .env
```

### 3. Run

**Interactive mode** — ask questions about documents in a conversation:
```bash
goose run --recipe recipe.yaml
```

**Headless mode** — answer a specific question:
```bash
goose run --recipe recipe.yaml --params question="What was the total public debt in FY2020 in nominal dollars?"
```

**Benchmark mode** — evaluate against OfficeQA (requires Docker):
```bash
# Pull the Treasury Bulletin corpus
docker pull ghcr.io/sentient-agi/harbor/officeqa-corpus:latest

# Run evaluation on 20 questions
python3 scripts/standalone_eval.py --limit 20

# Full benchmark (246 questions, ~4 hours, ~$12)
python3 scripts/standalone_eval.py
```

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  Goose Runtime                    │
│         (auto-compaction at 80% context)          │
│                                                   │
│  ┌─────────────────────────────────────────────┐  │
│  │          Prompt Template (84 lines)          │  │
│  │  3 iron rules + workflow + formulas + traps  │  │
│  └─────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────┐  │
│  │         Domain Skills (138 lines)            │  │
│  │  retrieval strategy + table parsing + CPI    │  │
│  └─────────────────────────────────────────────┘  │
│                       │                           │
│              Model: MiniMax M2.5                  │
│              (via OpenRouter)                     │
└──────────────────┬───────────────────────────────┘
                   │ grep/sed/python
          ┌────────▼────────┐
          │  Document Corpus │
          │  (697 TXT files) │
          └─────────────────┘
```

**Why Goose?** The agent harness was the single biggest performance breakthrough. Goose's auto-compaction at 80% context utilization preserves instruction fidelity across long multi-step reasoning chains. Without it, accuracy degrades from 80% early to 60% late in a run as tool outputs dilute the original instructions. With it, accuracy holds at 71-73% throughout. This also reduced cost by 87% ($14.50 to $1.85).

## How It Works

### The Three Iron Rules

These account for more accuracy gain than any other component:

1. **Write answer in every code block.** Every Python block ends with `open('/app/answer.txt','w').write(str(result))`. A rough answer beats an empty file. Removing this rule caused a 22-answer regression.

2. **All math in Python.** Uses scipy, numpy, statsmodels. Never computes in natural language. Prevents precision errors beyond the 1% tolerance.

3. **Stop after writing final answer.** No re-verification, no second-guessing. Prevents "self-sabotage" — overwriting a correct answer during an unnecessary check.

### 20+ Named Statistical Formulas

The prompt embeds exact implementations for: linear regression, t-statistic, Theil index, CAGR, YoY growth, continuously compounded growth, Expected Shortfall (CVaR), arc elasticity, HHI, Gini coefficient, coefficient of variation, hazard rate, Winsorized statistics, Box-Cox transform, HP filter, ARIMA, polynomial regression, and more.

### Domain Knowledge Injection

- **Unit conversion rules** — the #1 error pattern. Check four places: table title, header row, column header, footnotes.
- **Fiscal year conventions** — pre-1976 (Jul-Jun) vs post-1976 (Oct-Sep).
- **Treasury terminology traps** — "gross debt" vs "debt held by public", "receipts" vs "receipt instruments", "reported IN" vs "reported FOR".
- **CPI-U reference data** — embedded annual averages (1938-2020) for inflation adjustments.
- **Retrospective table strategy** — for multi-year questions, search the latest year first for a historical summary table.

## Methodology: EvoSkill, Done By Hand

Our optimization methodology parallels [Sentient's EvoSkill framework](https://github.com/sentient-agi/EvoSkill), which auto-discovers agent skills from failed trajectories. EvoSkill improved OfficeQA accuracy from 60.6% to 67.9%. We applied the same core loop manually and achieved **71.5%**:

```
                    ┌───────────────────┐
                    │  Submit agent run  │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │  Classify failures │
                    │  retrieval │       │
                    │  extraction │      │
                    │  computation │     │
                    │  behavioral        │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │  Prioritize by EV  │
                    │  (questions × P ×  │
                    │   score impact)    │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │  Create new skill  │
                    │  (formula, trap,   │
                    │   reference data)  │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │  Evaluate + keep/  │
                    │  revert (>5 var.)  │
                    └────────┬──────────┘
                             │
                             └──────────► repeat
```

**Cross-submission variance analysis** across 6 runs revealed:
- 114 always-pass questions (46.3%) — reliable base, don't regress these
- 43 always-fail questions (17.5%) — structural gaps, target these with new skills
- 89 swing questions (36.2%) — variance-driven, not directly addressable

The always-fail analysis identified specific missing formulas and reference data, which we added as targeted skills. This is exactly the EvoSkill hypothesis: **agent skills can be systematically discovered from failure patterns.**

See [`FINAL_REPORT.md`](FINAL_REPORT.md) for the full research paper with methodology, ablations, and results.

## Enterprise Use Cases

The capabilities validated on OfficeQA directly transfer to:

**Financial Services** — SEC filing analysis, credit research, regulatory reporting. The agent parses hierarchical financial tables, handles unit conversions, and computes ratios across multi-year filings.

**Government & Public Sector** — Budget analysis, GAO auditing, FOIA response. Validated on 86 years of actual government documents with fiscal year reasoning built in.

**Audit & Compliance** — Cross-document verification, variance analysis, financial statement reconciliation. Full reasoning traces provide auditability.

**Insurance & Actuarial** — Loss reserving, risk assessment. Native computation of CVaR, hazard rates, HHI, regression, and ARIMA from extracted document data.

## Key Findings

| Finding | Evidence |
|---------|----------|
| Prompt density > prompt volume | 84 lines outperformed 543 lines by +2.4% accuracy |
| Agent harness > prompt engineering | Goose vs OpenHands SDK = +5 correct answers, zero prompt changes |
| "Write answer in every block" is load-bearing | Removing it = -22 answers (8.9% regression) |
| MoE models need domain knowledge, not tutorials | MiniMax M2.5: #1 tool calling (76.8%), but 38% on FinanceAgent |
| Context management is a first-order variable | Without compaction: 80% early, 60% late. With: 71-73% throughout |
| Infrastructure load affects benchmarks | 2 AM: 171s latency, 69.5% accuracy. Daytime: 210s, 66.1% |

## Repository Structure

```
dolores-docagent/
├── recipe.yaml                  # Goose recipe — run this
├── arena.yaml                   # Sentient Arena config
├── prompts/
│   └── goose_prompt.j2          # 84-line prompt template (the core IP)
├── skills_consolidated/
│   └── core/SKILL.md            # 138-line domain knowledge package
├── skills/                      # Extended skills (542 lines, 5 files)
├── scripts/
│   ├── standalone_eval.py       # Docker-based evaluation
│   └── aggregate_results.py     # Results analysis
├── officeqa_full.csv            # OfficeQA ground truth (246 questions)
├── FINAL_REPORT.md              # Full research paper
├── SUBMISSION_REPORT.md         # Competition report
└── program.md                   # AutoResearch self-improvement loop
```

## Sentient Arena Context

This agent was developed during [Sentient Arena](https://arena.sentient.xyz) Cohort 0 — a two-week competition stress-testing enterprise AI agents on the OfficeQA benchmark. All participants used the same model (MiniMax M2.5) and corpus, isolating behavioral engineering as the sole variable.

Sentient's ecosystem includes:
- **[Arena](https://arena.sentient.xyz)** — Production-grade evaluation for enterprise AI agents
- **[ROMA](https://github.com/sentient-agi/ROMA)** — Recursive Open Meta-Agent framework (5K+ stars)
- **[EvoSkill](https://github.com/sentient-agi/EvoSkill)** — Auto-discovers agent skills from failed trajectories
- **[OpenDeepSearch](https://github.com/sentient-agi/OpenDeepSearch)** — Open-source search that outperforms Perplexity
- **[GRID](https://sentient.xyz/grid)** — Planetary-scale network connecting 40+ agents

Our methodology validates EvoSkill's core thesis and demonstrates it can be applied to achieve state-of-the-art results on enterprise document reasoning.

## Adapting to Your Own Documents

To use this agent on your own document corpus:

1. **Prepare your corpus** — convert documents to text files in a directory
2. **Edit the prompt template** — replace Treasury-specific traps with your domain knowledge
3. **Keep the iron rules** — the three behavioral rules are domain-agnostic
4. **Keep the formulas** — the statistical formula library is reusable
5. **Run the EvoSkill loop** — submit, classify failures, add targeted skills, repeat

The domain-specific content (fiscal year rules, Treasury terminology, CPI data) is clearly sectioned in the prompt and skills files for easy replacement.

## Citation

```bibtex
@misc{liu2026behavioral,
  title={Behavioral Engineering for Grounded Reasoning: A Systematic Approach to Enterprise Document QA},
  author={Liu, Leon (柳文浩)},
  year={2026},
  note={Dolores Research. Sentient Arena Cohort 0, \#1 on leaderboard.
        70.7\% accuracy on OfficeQA with MiniMax M2.5 (10B active params).}
}
```

## License

MIT License. See [LICENSE](LICENSE).

---

**[Dolores Research](https://doloresresearch.com)** — Behavioral engineering for enterprise AI agents.
