# Sentient Arena Cohort 0 — Genesis Project Document

**Author:** Leon (柳文浩), Founder — Dolores Research  
**Created:** March 22, 2026  
**Status:** Active Competition  
**Location:** Presidio, San Francisco  

---

## 1. Mission Statement

Place as high as possible in Sentient Arena Cohort 0 by building the best-performing AI agent for the OfficeQA benchmark. A strong placement serves two purposes: it validates Dolores Research's core thesis that the performance gap between expensive and cheap models is behavioral rather than capability-based, and it demonstrates production-ready AI orchestration methodology to the exact investor audience (Founders Fund, Pantera, Franklin Templeton) that Dolores Research needs for its early capital raise.

---

## 2. What Sentient Arena Is

Sentient is an open-source AI lab associated with the Sentient Foundation (a nonprofit). Key people include Sandeep Nailwal (Polygon co-founder) and academics like Pramod Viswanath (Princeton) and Himanshu Tyagi (IISc). They have a token ($SENT) and a broader ecosystem that includes The GRID (a network for AI agents), ROMA (a recursive open meta-agent framework built on DSPy), Dobby (a crypto-native open-source model), and OML (a framework for open-source model ownership).

Arena is Sentient's live testing environment for stress-testing enterprise-grade AI agents. It is not a standard benchmark — it simulates real-world enterprise chaos with incomplete information, long context, ambiguous instructions, and conflicting sources. Arena records full reasoning traces, not just final answers, so engineering teams can analyze how decisions were reached and pinpoint failures. It is vendor-agnostic, meaning teams can compare approaches across different models and toolchains.

### Cohort 0 Participants and Backers

The inaugural cohort includes Founders Fund, Pantera, and Franklin Templeton (collectively managing over $1.5T AUM), along with alphaXiv, Fireworks, OpenRouter, and OpenHands. OpenHands is supporting participants with their Software Agent SDK, and OpenRouter is providing inference infrastructure.

### What the Backers Care About

Julian Love (Franklin Templeton): "The question is no longer whether these systems are powerful, but whether they are reliable in real-world workflows." He wants to distinguish "ideas with potential" from "true production-ready capabilities."

Himanshu Tyagi (Sentient co-founder): "Companies need to know: in production environments, where the cost of failure is high and trust is fragile, can agents still reason reliably?"

The findings from Cohort 0 will be documented and open-sourced.

---

## 3. The OfficeQA Benchmark — Complete Understanding

### What It Is

OfficeQA is a grounded reasoning benchmark created by Databricks (specifically their Mosaic Research team), designed to test AI agents on real-world enterprise document reasoning. It was built in partnership with USAFacts and uses the U.S. Treasury Bulletin archive as its document corpus. The benchmark evaluates how well AI systems can retrieve information from complex documents, parse dense financial tables, and perform analytical reasoning to produce precise numerical answers.

### The Corpus

The document corpus consists of U.S. Treasury Bulletins spanning 1939 to 2025. These are government financial publications describing the operations of the U.S. Treasury — where money came from, where it is, where it went, and how it financed operations. The total dataset comprises approximately 89,000 pages across 696 PDF files (~20GB). Each individual bulletin is 100-200 pages long and contains prose, complex tables, charts, and figures.

There are two distinct document populations. Pre-1996 bulletins are scans of physical documents (essentially photographs of printed pages where table structure must be inferred visually). Post-1996 bulletins are digitally produced PDFs with extractable text, but still feature complex layouts. Importantly, Databricks strips the existing OCR layer from all PDFs because the existing OCR quality is too low. This means the competition environment likely presents agents with raw scans that they must interpret directly.

### Available Document Formats (from the GitHub repo)

The `databricks/officeqa` repository provides the corpus in three formats, and understanding which format your agent uses is the single highest-impact variable:

**Raw PDFs** (`treasury_bulletin_pdfs/`, ~20GB): The original documents as downloaded from the Federal Reserve Archive. 696 PDF files. Use these if your system can process PDFs directly.

**Parsed JSON** (`treasury_bulletins_parsed/jsons/`, ~600MB): PDFs processed through Databricks' `ai_parse_document`. Contains full structural information including bounding boxes, tables as HTML, and element-level metadata. Distributed as zip archives.

**Transformed TXT** (`treasury_bulletins_parsed/transformed/`, ~200MB): The JSON files simplified into a text format where tables are converted to Markdown. Described as "more readable for LLMs." This is the format that produced the biggest performance gains in Databricks' evaluations.

The repository also includes transformation scripts in `treasury_bulletins_parsed/transform_scripts/` that can produce alternative representations from the parsed JSON, including a page-level marker version (`transform_files_page_level.py`).

### The Questions

OfficeQA consists of 246 questions organized into two difficulty levels:

**OfficeQA Full** (N=246): The complete benchmark, including both easy and hard questions. This is what Arena uses. It is described as "a version of the benchmark containing additional easier questions to hillclimb systems on."

**OfficeQA Pro** (N=133): A subset containing only the hard questions. This is the default for evaluating frontier models in the research paper.

"Easy" questions are defined as questions that both frontier agent systems got correct. "Hard" questions are questions that at least one agent answered incorrectly.

Questions on average require information from approximately 2 different Treasury Bulletin documents. Human solvers averaged 50 minutes per question, with the majority of time spent locating the right information across the corpus. None of the questions require more than high school math, though some financial or statistical terms may need to be looked up.

To ensure questions require document-grounded retrieval, Databricks filtered out any questions that LLMs could answer using parametric knowledge alone or via web search. Even seemingly complex questions (like computing a t-statistic for WWII-era Treasury bond rates) were filtered if models could answer from memorized training data.

### Dataset Schema

Each row in `officeqa_full.csv` contains:

| Column | Description |
|--------|-------------|
| `uid` | Unique question identifier |
| `question` | The question to answer |
| `answer` | Ground truth answer |
| `source_docs` | Original URL(s) from the Federal Reserve Archive |
| `source_files` | Corresponding parsed filename(s), e.g. `treasury_bulletin_1941_01.txt` |
| `difficulty` | `easy` or `hard` |

The `source_files` column is critical for the self-improvement loop — it tells you exactly which documents contain the answer, enabling precise diagnosis of retrieval vs. parsing vs. reasoning failures.

### File Naming Convention

URL format: `https://fraser.stlouisfed.org/title/treasury-bulletin-407/{MONTH}-{YEAR}-{ID}?page={PAGE}`  
Filename format: `treasury_bulletin_{YEAR}_{MONTH_NUM}.{ext}`  
Example: January 1941 → `treasury_bulletin_1941_01.txt`

### Question Types (Three Distinct Categories)

**Type 1 — Direct Value Lookup:** Find a specific value in a specific document for a specific time period. Example: "What were the total expenditures (in millions of nominal dollars) for U.S national defense in the calendar year of 1940?" Traps include fiscal-year-vs-calendar-year confusion (the table may show fiscal year totals but the question asks for calendar year, requiring monthly summation), unit ambiguity, and document versioning.

**Type 2 — Multi-Document Analytical Reasoning:** Requires finding data across multiple bulletins, extracting a time series, and performing statistical or mathematical computation. Example: "Predict the total outlays of the US Department of Agriculture in 1999 using annual data from the years 1990-1998 (inclusive). Use a basic linear regression fit..." These questions demand precise computation (Python, not mental math) and careful attention to detailed formatting instructions in the question.

**Type 3 — Visual Reasoning (~3% of questions, ~7 questions):** Questions referencing charts, graphs, or figures that require visual interpretation. Example: "How many local maxima are there on the line plots on that page?" All tested agents currently fail on these. Deprioritize — the ROI of solving these is low relative to the other 239 questions.

### Scoring System

Fuzzy numeric matching with configurable tolerance. Arena uses 1% tolerance. The `reward.py` evaluation script computes the absolute relative error between the agent's answer and the ground truth. If the ground truth is X and the agent answers Y, the relative error is |X - Y| / |X|. An answer is correct if this error is ≤ 0.01 (1%).

This tolerance means you don't need to nail every last digit, but extraction errors can cascade through derived computations. A single misread value in a 9-point time series for a linear regression can push the final answer well beyond 1% tolerance.

### Baseline Performance Numbers

These numbers from Databricks' evaluations define the competitive landscape:

| Configuration | Accuracy (0% error) |
|--------------|---------------------|
| Frontier LLMs, no document access | ~2% |
| Frontier LLMs, web search only | <12% |
| GPT-5.1 Agent, raw PDFs | ~37.4% |
| Claude Opus 4.5 Agent, raw PDFs | ~43.5% |
| GPT-5.1 Agent, Databricks-parsed docs | ~52.8% |
| Claude Opus 4.5 Agent, Databricks-parsed docs | ~67.8% |
| GPT-5.1, oracle parsed pages (non-agentic) | ~70% |

The jump from raw PDFs to parsed documents is the largest single performance delta in the entire benchmark: +30.4 percentage points for Claude (an 81.7% relative increase). This confirms that document parsing quality is the dominant variable.

The ~70% ceiling with oracle pages represents the upper bound assuming perfect retrieval and optimal parsing. The remaining ~30% gap comes from questions requiring web search (~13%), computational reasoning errors, parsing errors in complex tables, and visual reasoning questions.

**Scoring above 70% would be exceptional. Getting to 60%+ is achievable with good engineering.**

### Five Documented Failure Modes

These are from Databricks' error analysis and form the basis of your optimization roadmap:

**1. Table Parsing Errors (Highest Impact).** Complex tables with nested column hierarchies, merged cells, and unusual formatting produce misaligned or incorrectly extracted values. Column shifts during automated extraction can cause values to be attributed to wrong headers entirely. Treasury Bulletin tables use hierarchical row AND column headers — a cell's meaning depends on reading both its row header (often indented to show hierarchy) and its column header (which may span multiple sub-columns).

**2. Document Versioning Ambiguity.** Treasury Bulletins are frequently revised and reissued. Multiple legitimate values may exist for the same data point depending on which publication date the agent references. Agents often stop searching once they find a plausible answer, missing the most authoritative or up-to-date source. Example: total public debt securities figures differ between the June 2010 and September 2010 bulletins by 21 million dollars due to revisions.

**3. Fiscal Year vs. Calendar Year Confusion.** The U.S. federal fiscal year starts in October (since 1976; it was July before that). Questions may ask about "calendar year 1940" but tables display fiscal year totals. The agent must check whether the time period definition in the question matches the time period definition in the table, and sum monthly values if they differ.

**4. Unit Confusion.** Values appear in different units across tables and eras — "millions of dollars," "thousands of dollars," raw dollar amounts. Unit indicators can appear in the table title, a header row, a column header, or a footnote, and their placement is inconsistent across decades of publications.

**5. Visual Comprehension (~3% of questions).** Charts and graphs requiring visual reasoning. All current agents fail. Low priority for optimization.

---

## 4. Arena Competition Mechanics

### What You Build

You configure a pre-built coding agent to perform well on the OfficeQA benchmark. No custom Python pipeline coding required. Everything is configured through a single `arena.yaml` file.

### Available Coding Agents

You pick one of: **Codex**, **OpenHands**, **Goose**, or **OpenCode**. OpenHands is recommended as a starting point because the guide explicitly mentions OpenHands is "supporting participants with their Software Agent SDK."

### Your Levers for Improvement

**1. Prompt Engineering** — Write a Jinja2 prompt template (`prompts/officeqa_prompt.j2`) that guides the agent's methodology for finding and extracting data from Treasury Bulletins. This is the highest-impact lever after document format selection.

**2. Skills Files** — Provide reference files in `skills/` that the agent can use as additional context while solving tasks. This is where domain knowledge, worked examples, and the failure catalog live. This is your "secret weapon" lever.

**3. Model Selection** — Choose the best model for the task via OpenRouter (e.g., `openai/gpt-5.3`, `anthropic/claude-sonnet-4-5-20250929`). The model needs strong document comprehension and code generation capabilities. Start with a faster/cheaper model for iteration, switch to the strongest for final runs.

**4. MCP Servers** — Give the agent additional tools via Model Context Protocol servers (filesystem access, search, custom APIs). A potential vector search MCP server for document retrieval could be high-value.

**5. Agent-Specific Config** — Tune parameters like `reasoning_effort` and other agent-specific options.

### Getting Started

Download the CLI: `https://arena.sentient.xyz/api/download/cli`  
Authenticate: `arena auth`  
Get the template: `arena init`

---

## 5. Strategic Analysis

### Why BOTCOIN Experience Maps Directly

The BOTCOIN proof-of-inference mining challenges are structurally almost identical to OfficeQA. Both involve synthetic/complex documents with structured data, multi-constraint questions requiring precise numerical answers, and cascading error risks where one wrong extraction breaks downstream computations.

The failure modes from Leon's three failed BOTCOIN attempts map directly onto Databricks' documented OfficeQA failure modes:

| BOTCOIN Failure | OfficeQA Equivalent |
|----------------|---------------------|
| Number qualifier ambiguity ("just under X" = X-1) | Unit confusion, fiscal vs. calendar year |
| Cascading errors from single wrong value | Precision divergence through derived computations |
| Near-ties (two companies within 0.01%) | Document versioning (multiple valid values) |
| Token/time expiration from manual reasoning | Agent timeout from inefficient retrieval |

The four-phase architecture developed for BOTCOIN — **Extraction → Computation → Validation → Submission** — is exactly the methodology the Arena prompt template should teach the agent to follow. The difference is that in BOTCOIN, Leon wrote the Python pipeline directly. In Arena, Leon writes instructions that cause the agent to follow this same pipeline through prompt engineering and skills files.

### Why DeepRepo Is Relevant at the Thinking Level, Not the Architecture Level

Arena constrains the architecture — you configure a single pre-built agent, not a multi-agent orchestration system. DeepRepo's value here is conceptual, not implementational. The key DeepRepo-inspired insights to encode in the prompt are: decompose complex tasks into discrete phases (retrieval → extraction → computation → validation), verify intermediate results before proceeding, and use the right tool for each subtask (LLM for comprehension, Python for computation, structured validation for quality control).

### The Parsing Advantage is the #1 Strategic Priority

The single largest performance delta in the entire benchmark comes from document parsing quality: a 30+ percentage point improvement from raw PDFs to parsed documents. Your first action after running `arena init` must be to understand what document format the Arena environment provides and whether you can augment it with pre-parsed text files. If you can provide the transformed TXT files from the OfficeQA repo (or create your own parsed representations) via skills files or MCP servers, this alone could put you ahead of teams working with raw PDFs.

### The Self-Improvement Loop

The competition uses a fixed benchmark with 246 questions and ground truth answers, making it perfectly suited for iterative optimization. The loop structure:

1. Run agent on full benchmark, record score and per-question results.
2. For each wrong answer, classify the failure mode: retrieval failure (wrong document), parsing failure (right document, wrong value), computation failure (right values, wrong calculation), or interpretation failure (misunderstood the question). Use the `source_files` column to diagnose retrieval vs. other failures.
3. For the dominant failure category, make targeted improvements (to the prompt template, skills files, or agent config).
4. Maintain a growing "known pitfalls" file in `skills/` that the agent reads as context.
5. Track metrics per question across iterations to detect regressions.
6. Repeat, targeting 3-4 cycles per day during the optimization phase.

A friend in the cohort is using this same approach (described as a "self-improvement loop to get the right prompts"). The differentiator is how systematically you execute the loop and how effectively you diagnose and categorize failures.

---

## 6. Execution Plan (Two Weeks)

### Days 1-2: Setup and Reconnaissance
- Install Arena CLI, authenticate, run `arena init`.
- Examine the Arena environment: what document formats are provided? What's the file structure? What constraints exist?
- Study 5-10 sample questions manually against the actual Treasury Bulletin documents to build intuition.
- Pick your coding agent (start with OpenHands).
- Get a baseline score with minimal/default configuration.
- Download and study `officeqa_full.csv` to understand the question distribution.

### Days 3-5: Parsing Infrastructure (Highest ROI)
- Determine if pre-parsed documents can be provided to the agent (via skills files, MCP servers, or the environment itself).
- If possible, set up access to the transformed TXT files from the OfficeQA repo.
- Build a document retrieval strategy: create an index or search capability that maps question topics and time periods to specific document filenames.
- Consider setting up a vector search MCP server for semantic retrieval.
- Run 2-3 iteration cycles focused purely on improving retrieval accuracy.

### Days 6-8: Prompt Optimization
- Refine the Jinja2 prompt template based on failure analysis from days 3-5.
- Encode the four-phase methodology (retrieval → extraction → computation → validation) into the prompt.
- Add question-type-specific strategies (direct lookup vs. multi-document analytical reasoning).
- Build out the known pitfalls skills file with specific failure patterns observed.
- Create a Treasury Bulletin structure guide as a skills file (how tables are organized, where unit indicators appear, fiscal year conventions).
- Run 3-4 iteration cycles per day, targeting the most common failure modes.

### Days 9-11: Hard Questions and Edge Cases
- Focus specifically on the "hard" question subset (where differentiation happens — most teams will converge on easy questions).
- Analyze what makes hard questions hard and build specific handling strategies.
- Address document versioning issues (prompt the agent to check for revisions in later bulletins).
- Optimize for multi-document questions (ensure the agent gathers all required data before computing).
- Fine-tune computation instructions (explicit Python code generation for statistical operations).

### Days 12-13: Final Optimization and Submission Prep
- Switch to the strongest available model for final runs.
- Run a final iteration cycle on the full benchmark.
- Clean up configuration.
- Prepare writeup and narrative framing for the Dolores Research story.
- Document the methodology for the open-source findings component.

### Day 14: Buffer
- Something will break. Keep this clear.

---

## 7. Investor Narrative Framing

The honest and compelling story is not "I used multi-agent orchestration to win." The competition doesn't allow multi-agent systems. The story is:

**The same failure analysis methodology and systematic decomposition thinking that underlies Dolores Research's orchestration work proved to be the winning approach even when applied through prompt engineering rather than architectural orchestration.**

The specific framing: "We took a benchmark where frontier agents score 34-43% and achieved X% through systematic behavioral engineering. This validates the Dolores Research thesis — the performance gap between expensive and cheap models in orchestration is behavioral, not capability-based. You don't need a different model. You need the model to follow the right methodology. Teaching models the right behavioral patterns is what Dolores Research does, whether through multi-agent orchestration (DeepRepo), autonomous fine-tuning (RLM Distiller), or prompt-driven behavioral engineering (Arena)."

This framing is stronger than a pure architecture story because it shows the thesis is general — it works across different implementation contexts. Investors want robust, broadly applicable theses, not ones that only work in one narrow architecture.

---

## 8. Key Links and References

- **Arena CLI Download:** https://arena.sentient.xyz/api/download/cli
- **OfficeQA GitHub Repo:** https://github.com/databricks/officeqa
- **OfficeQA Technical Report:** https://arxiv.org/abs/2603.08655
- **Databricks Blog Post:** https://www.databricks.com/blog/introducing-officeqa-benchmark-end-to-end-grounded-reasoning
- **Treasury Bulletin Archive (Federal Reserve):** https://fraser.stlouisfed.org/title/treasury-bulletin-407?browse=1930s
- **ROMA GitHub:** https://github.com/sentient-agi/ROMA
- **Sentient Arena Sign-in:** https://arena.sentient.xyz/sign-in

---

## 9. Open Questions (To Resolve During Reconnaissance)

These questions need to be answered during Days 1-2 after running `arena init`:

1. What document format does the Arena environment provide? Raw PDFs only, or also parsed versions?
2. Can you augment the agent's environment with pre-parsed text files from the OfficeQA repo?
3. What is the exact structure of the `arena.yaml` configuration file? What parameters are available?
4. What does the Jinja2 prompt template receive as variables? Just the question text, or also metadata?
5. How are MCP servers configured in the Arena environment? What's the latency/reliability?
6. How does scoring work in the competition? Is it purely accuracy on the 246 questions, or are there other factors (reasoning trace quality, cost, latency)?
7. Can you see per-question results after each submission, or only the aggregate score?
8. How many submissions are allowed? Is there a rate limit on iteration cycles?
9. What models are available through OpenRouter in the Arena environment?
10. How does the agent interact with the document corpus? Does it have filesystem access, or does it go through an API?

---

## 10. Failure Catalog (Living Document)

This section will grow throughout the competition as failure patterns are identified and cataloged. Each entry should record the question ID, the failure mode category, the specific error, and the fix applied. This catalog also feeds into the `skills/known_pitfalls.md` file that the agent reads as context.

### Template for Failure Entries

```
### Failure #[N]
- **Question ID:** [uid]
- **Question:** [text]
- **Expected Answer:** [ground truth]
- **Agent Answer:** [what the agent returned]
- **Category:** [retrieval | parsing | computation | interpretation | visual]
- **Root Cause:** [specific description]
- **Fix Applied:** [what was changed in prompt/skills/config]
- **Fix Effective:** [yes/no/partial — did the next iteration get this question right?]
```

### Iteration Score Tracking

| Iteration | Date | Score (%) | Easy Correct | Hard Correct | Primary Changes |
|-----------|------|-----------|-------------|-------------|-----------------|
| 0 (baseline) | | | | | Default config |
| 1 | | | | | |
| 2 | | | | | |

---

*This is a living document. Update it as new information emerges from the Arena environment, from iteration results, and from competitive intelligence.*
