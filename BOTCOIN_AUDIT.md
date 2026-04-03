# BOTCOIN Architecture Audit for Sentient Arena / OfficeQA

## Section 1: Architecture Overview

The BOTCOIN mining system is a four-phase pipeline that transforms an unstructured natural-language document about 25 fictional companies into a single-line constrained artifact string, then submits it on-chain for reward credits. The architecture is instructive because it solves a problem structurally identical to OfficeQA: extract precise numerical data from prose, answer multi-hop questions over that data, and produce a verified answer under strict correctness constraints.

### Pipeline Phases

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Phase 1: EXTRACTION                                                       │
│   Input:  Raw prose document (markdown) + list of 25 company names        │
│   Output: Structured CompanyRecord[] with typed fields                    │
│   Method: Two paths —                                                     │
│     (a) Rule-based regex parser (extract_financial_dossier,               │
│         extract_regulatory_filings)                                       │
│     (b) LLM-based extraction via OpenAI structured output                 │
│         (extract_companies_with_openai)                                   │
│   Boundary: This is where unstructured → structured happens               │
├───────────────────────────────────────────────────────────────────────────┤
│ Phase 2: COMPUTATION                                                      │
│   Input:  CompanyRecord[] + list of questions                             │
│   Output: AnswerResult[] mapping each question to a company name          │
│   Method: Two paths —                                                     │
│     (a) Rule-based solver (solve_financial_dossier) using hardcoded       │
│         question-pattern matchers                                         │
│     (b) Plan-driven solver (solve_challenge) using LLM-generated          │
│         execution plans with filter/rank operations                       │
│   Boundary: Pure Python computation — no LLM calls                        │
├───────────────────────────────────────────────────────────────────────────┤
│ Phase 3: ARTIFACT CONSTRUCTION + VALIDATION                               │
│   Input:  AnswerResult[] + constraint list                                │
│   Output: ArtifactCandidate[] — each is a single-line string satisfying   │
│           all constraints (word count, acrostics, primes, equations,       │
│           banned letters, required tokens)                                │
│   Method: Deterministic constraint assembly (build_dossier_artifact)       │
│           + validation (validate_dossier_artifact)                         │
│   Key: Generates multiple candidates when near-ties exist, validates all  │
├───────────────────────────────────────────────────────────────────────────┤
│ Phase 4: SUBMISSION + ON-CHAIN RECORDING                                  │
│   Input:  Artifact string + auth token + challenge metadata               │
│   Output: Pass/fail result, on-chain receipt transaction                  │
│   Method: HTTP API calls to coordinator, then Bankr transaction submit    │
│   Timing: Auth happens AFTER artifact is built (token TTL = 10 min)       │
└───────────────────────────────────────────────────────────────────────────┘
```

### Critical Architectural Decision: LLM vs. Programmatic

The single most important design decision in this codebase is the **strict boundary between LLM reasoning and programmatic computation**. The LLM is used only for extraction (Phase 1) — turning prose into structured data. All question-answering, metric computation, filtering, ranking, and constraint satisfaction happen in deterministic Python code. This was an explicit lesson learned from three failed attempts where pure LLM reasoning produced precision errors:

> "Previous mining attempts (Claude Opus 4.6) failed 3/3 challenges. Root causes were precision failures, not reasoning failures. DO NOT attempt to solve via pure LLM reasoning." — `AGENTS.md:73`

This maps directly to the OfficeQA challenge: the 30+ percentage point gap between raw-PDF agents (~43.5%) and pre-parsed agents (~67.8%) is fundamentally the same problem. The LLM should extract; the code should compute.

### Data Flow: What Goes In, What Comes Out

The `CompanyRecord` dataclass (`solver.py:72-87`) is the central data structure. It holds:

```python
@dataclasses.dataclass
class CompanyRecord:
    canonical_name: str        # Exact name from challenge company list
    aliases: list[str]         # Ticker symbols and natural aliases
    employees: int | None      # Headcount, qualifier-adjusted
    employee_qualifier: str | None  # "just_under", "approximately", etc.
    employees_raw: str | None  # Original text for audit trail
    revenue_millions: float | None  # Total annual revenue (sum of quarters)
    revenue_qualifier: str | None
    revenue_raw: str | None
    hq_city: str | None
    hq_country: str | None
    hq_country_code: str | None
    ceo_first: str | None
    ceo_last: str | None
    metadata: dict[str, Any]   # Holds quarterly breakdowns, ratios, founding year, etc.
```

The metadata dict carries structured sub-fields: `quarterly_revenue_millions` (q1-q4), `quarterly_growth_pct` (q1-q4), `de_ratio`, `satisfaction_rating`, `founded_year`, `public` (bool), `ipo_year`, and `parse_notes` for flagging extraction issues.

For OfficeQA, the equivalent would be a structured record per table row or document section, with typed numerical fields, unit annotations, and source provenance.

---

## Section 2: Extraction Pipeline Deep Dive

### Two Extraction Strategies

**Strategy A: LLM-Based Extraction** (`extract_companies_with_openai`, line 722)

Uses OpenAI's structured output (JSON schema enforcement) to extract company data. The prompt instructs:

```
- Use the exact company names from the provided companies array as canonical_name.
- Preserve raw number phrases exactly in employees_raw and revenue_millions_raw.
- Do not round. Do not reinterpret qualifiers in the JSON.
- If a field is missing, return null.
```

The extraction schema (`extraction_schema`, line 618) enforces typed fields via JSON schema, requiring `canonical_name`, `aliases`, `employees_raw`, `revenue_millions_raw`, `hq_city`, `hq_country`, `hq_country_code`, `ceo_first`, `ceo_last`, and `metadata`. The key design choice is preserving **raw strings** (`employees_raw`, `revenue_millions_raw`) alongside parsed values — this enables post-hoc qualifier processing in Python rather than trusting the LLM to do arithmetic.

**Strategy B: Rule-Based Regex Extraction** (`extract_financial_dossier`, line 1200; `extract_regulatory_filings`, line 1436)

The regex parser handles two known document formats:

1. **Financial Dossier** format — detected by `"leadership dossiers"` in the document. Uses 8 compiled regex patterns:
   - `DOSSIER_FORMAL_LEADER_RE` — captures CEO name, company, ticker alias, HQ city/country from `**Name** — Title, Company (TICKER). HQ: City, Country.`
   - `DOSSIER_RUNS_LEADER_RE` — captures the same from `**Name** runs Company out of City, Country.`
   - `DOSSIER_FULL_QUARTERLY_RE` / `DOSSIER_ALIAS_QUARTERLY_RE` — quarterly revenue and growth data
   - `DOSSIER_FULL_RATIO_RE` / `DOSSIER_ALIAS_RATIO_RE` — D/E ratio, satisfaction rating, headcount
   - `DOSSIER_FULL_FOUNDING_RE` / `DOSSIER_ALIAS_FOUNDING_RE` — founding year, IPO status

2. **Regulatory Filings** format — detected by `"consolidated regulatory filings"`. Parses line-by-line structured data: `FILING:`, `ENTITY:`, `OFFICER:`, `RATIOS:`, `DISCLOSURE:`, `REVENUE:`, `GROWTH:`, `FINANCIALS:` prefixed lines.

### Qualifier Handling: The Most Critical Extraction Pattern

The `SUPPORTED_QUALIFIERS` dictionary (`solver.py:30-38`) and `parse_qualified_number` function (`solver.py:197-212`) encode exact rules for ambiguous numeric expressions:

```python
SUPPORTED_QUALIFIERS = {
    "just under": ("just_under", -1),   # "just under 53099" → 53098
    "just over": ("just_over", 1),       # "just over 100" → 101
    "approximately": ("approximately", 0), # "approximately X" → X
    "roughly": ("roughly", 0),
    "close to": ("close_to", 0),
    "about": ("about", 0),
    "nearly": ("nearly", 0),            # "nearly X" → X
}
```

This was the **number one failure mode** in the initial attempts — a single digit error from misinterpreting "just under 53099" cascades through all downstream computations. The fix was to hardcode these rules and apply them deterministically rather than relying on the LLM to interpret them.

**OfficeQA Translation:** Treasury Bulletins won't use "just under" but they do use units like "in millions of dollars", "in thousands", footnotes like "revised" or "preliminary", and fiscal year notations. The same pattern applies: define explicit rules for each qualifier/unit indicator and apply them programmatically after extraction.

### Alias Resolution: A Multi-Pass Algorithm

The most sophisticated extraction pattern is alias resolution (`solver.py:1142-1336`). Companies are referenced by full name ("Byte Materials"), ticker alias ("BM"), or natural alias ("Byte"). When parsing alias-attributed data, the system:

1. Builds lookup tables mapping each alias to candidate companies
2. Attempts to resolve each alias fact to a company by matching existing known facts
3. If ambiguous (multiple candidates), defers to a later pass
4. Runs up to 4 resolution passes, stopping when no progress is made
5. Falls back to hardcoded disambiguation for known edge cases (lines 1319-1328)

The `record_conflicts` function (`solver.py:1189-1197`) logs when an alias-attributed value conflicts with an existing value, maintaining an audit trail in `parse_notes`.

### Revenue Parsing: Handling Units and Growth

`parse_million_amount` (`solver.py:1015-1033`) handles unit conversion:

```python
multiplier = 1000.0 if "billion" in trimmed.lower() else 1.0
return (numeric * multiplier) + offset, qualifier, raw
```

`parse_growth_value` (`solver.py:1036-1050`) handles growth expressions:
- "remained flat" / "was unchanged" → 0.0
- Explicit signs: `+5%` / `-3%`
- Directional words: "fell", "declined", "contracted" negate the value

### Normalization Steps

- `normalize_string` (`solver.py:184`): strips whitespace, collapses multiple spaces, casefolds
- `normalize_key` (`solver.py:188`): removes all non-alphanumeric characters for fuzzy matching
- `normalize_nullable_string` (`solver.py:851`): trims and optionally uppercases
- Company name canonicalization: extracted names are matched against the challenge's company list using `normalize_key` comparison

### Error Handling for Malformed Content

- Missing fields are tracked per-company and reported in `notes` (lines 1358-1378)
- `parse_notes` on each company record logs parsing warnings
- Quarterly data requires exactly 4 segments; mismatches are flagged
- Revenue/growth parsing failures are noted but don't halt the pipeline — null values propagate and cause failures at the computation stage where they can be caught cleanly

---

## Section 3: Computation Pipeline Deep Dive

### Question Classification and Metric Selection

The `determine_question_metric` function (`solver.py:2018-2054`) maps natural language question patterns to programmatic metric functions. It uses keyword matching:

```python
if "employees divided by full-year revenue" in lowered:
    return lambda company: (company.employees or 0) / (company.revenue_millions or 1), True, ...
if "revenue volatility" in lowered:
    return revenue_volatility, True, ...
if "ipo'd most recently" in lowered:
    return lambda company: company_meta(company, "ipo_year"), True, ...
```

Supported metrics include:
- **Ratio calculations**: employees/revenue, satisfaction + average growth
- **Aggregations**: total revenue (sum of quarters), revenue volatility (max - min quarterly)
- **Temporal**: most recent IPO, founding decade filtering
- **Multi-dimensional**: combined satisfaction + growth score

### Filtering Pipeline

`filter_rule_companies` (`solver.py:1944-2015`) chains multiple filters from question text:

```python
# Public/private status
if "publicly traded" in lowered:
    filtered = [c for c in filtered if company_meta(c, "public") is True]

# Founding decade
decade_match = re.search(r"founded in the (\d{4})s", lowered)
if decade_match:
    start_year = int(decade_match.group(1))
    filtered = [c for c in filtered if start_year <= (company_meta(c, "founded_year") or -1) <= start_year + 9]

# Growth conditions
if "positive growth in every quarter" in lowered:
    filtered = [c for c in filtered if all((quarter_growth(c, i) or 0) > 0 for i in range(1, 5))]

# Numeric thresholds
de_match = re.search(r"d/e\s*(?:under|below)\s*([0-9.]+)", ...)
if de_match:
    filtered = [c for c in filtered if (company_meta(c, "de_ratio") or 9999) < threshold]
```

### Ranking with Near-Tie Detection

`rank_answer` (`solver.py:1687-1736`) sorts candidates by metric and selects the top entry. Critically, it detects near-ties using `numeric_relative_difference`:

```python
diff_pct = numeric_relative_difference(selected_score, neighbor_score) * 100
if diff_pct <= tie_margin_pct:
    warnings.append(f"Tie/near-tie within {tie_margin_pct:.2f}%...")
    alternates.append(AnswerCandidate(...))
```

When near-ties are detected, the system generates multiple artifact candidates using `expand_answer_combinations` (`solver.py:2364-2375`), producing up to `max_candidates` (default 4) alternate solutions.

### Plan-Driven Computation (LLM-Generated Plans)

The alternative computation path uses LLM-generated execution plans. The LLM produces a `QuestionPlan` specifying:
- `strategy`: always "rank" (sort and select)
- `metric`: a composable expression tree with kinds `field`, `ratio`, `arithmetic`, `literal`
- `filters`: declarative filter specs with ops `eq`, `neq`, `contains`, `startswith`, `in`
- `order`: `asc` or `desc`
- `rank`: which position to select (1 = top)

The `evaluate_expression` function (`solver.py:2266-2303`) recursively evaluates metric expressions:

```python
if kind == "field":
    return safe_float(resolve_field(company, str(spec["field"])))
if kind == "ratio":
    left = evaluate_expression(company, company_map, dict(spec["numerator"]))
    right = evaluate_expression(company, company_map, dict(spec["denominator"]))
    return left / right
if kind == "arithmetic":
    # Supports: add, sub, mul, div, mod
```

### Precision Handling

- All numeric comparisons use `safe_float` and `safe_int` which strip non-numeric characters and handle edge cases
- `format_score` strips trailing zeros: `f"{value:.6f}".rstrip("0").rstrip(".")`
- Modular arithmetic uses `int()` coercion: `float(int(left) % int(right))`
- Revenue is always stored in millions as float; employees as int
- Near-tie detection uses relative difference with configurable margin (default 1%)

### Patterns Directly Reusable for OfficeQA

1. **Filter-then-rank pattern**: Parse question → extract filter criteria → filter dataset → compute metric → rank → select. This is the core computation loop for any tabular QA system.
2. **Composable expression evaluation**: The `evaluate_expression` tree supports arbitrary metric composition. For OfficeQA, this could handle "ratio of 2024 value to 2020 value" or "average annual growth rate over 5 years."
3. **Near-tie detection with alternate candidates**: When values are close, generate multiple answers and try each. This directly addresses the 1% tolerance threshold in OfficeQA.

---

## Section 4: Validation and Constraint Checking

### Pre-Submission Validation

`validate_dossier_artifact` (`solver.py:1870-1941`) runs a comprehensive constraint check suite:

1. **Exact word count**: Splits on spaces, compares to required count
2. **Single line**: Checks for absence of newline characters
3. **Required tokens**: Verifies HQ city, CEO last name, HQ country appear in artifact
4. **Prime number**: Recomputes `nextPrime((employees % modulus) + offset)` and checks inclusion
5. **Equation**: Recomputes `A+B=C` from quarter revenue values and checks inclusion
6. **Acrostic**: Verifies first letters of first N words match expected initials
7. **Banned letters**: Case-insensitive scan for forbidden characters
8. **Punctuation-only words**: Regex check `\W+` on each word

The plan-driven path has its own validation via `run_validation_checks` (`solver.py:2446-2508`):
- **Company name validation**: Each answer must match an entry in the challenge's company list
- **Required fields**: Checks that all fields needed by artifact construction exist
- **Artifact non-empty**: Basic sanity check
- **Artifact regex**: Pattern matching against expected format
- **Warning propagation**: Near-tie warnings are surfaced as validation failures

### Self-Correction Mechanism

The system doesn't retry a single question, but it does generate multiple artifact candidates when near-ties exist. `expand_answer_combinations` produces the Cartesian product of primary and alternate answers (capped at 4 candidates), and each candidate is independently validated. The candidate with all constraints passing is selected.

In the mining loop (`cmd_mine_rules`, line 2670), if a submission fails, the system requests a completely new challenge rather than retrying — this is a design choice acknowledging that the verifier is deterministic, so a wrong answer will always be wrong.

### Cascading Error Prevention

The architecture explicitly addresses cascading errors through:

1. **Dependency tracking in constraints**: Constraints reference question answers (e.g., "employees of the answer to Question 9"). If Q9 is wrong, every constraint depending on Q9 fails. The code handles this by making constraint computation depend on `selected_answers[index]` — changing one answer recomputes all dependent constraints.

2. **Missing data = wrong answer principle** (`AGENTS.md:95`): "If a constraint needs HQ country for your answer and it's not in the doc, your answer is wrong. Re-examine the question." The validation layer checks for null/missing fields before using them, and missing required fields are flagged as validation failures.

3. **Multiple candidate generation**: By producing alternate candidates, the system can recover from a single wrong answer that cascades. If Q4's answer is a near-tie, both options are tried, and the one where all constraints pass is selected.

---

## Section 5: Failure Analysis Archaeology

### Failure Timeline

The codebase records two mining batches with 5 total failed attempts before the successful solve:

### Batch 1: `batch-20260310-0545` — Three Failures

**Attempt 1** — Challenge `0xd07e089a...`
- **Error**: `"No candidates matched question 5"`
- **Root cause**: The rule-based parser extracted company data but left critical fields null. Question 5 asked "Among firms that remained private, which has the best satisfaction rating?" Many companies had `satisfaction_rating: null` because the alias resolution failed — ambiguous aliases like "Byte" mapping to multiple companies (Byte Materials, Byte Solutions, Byte Analytics) left data unassigned.
- **Evidence**: The `companies.json` file shows `parse_notes` entries like `"Unresolved alias reference Byte: candidates=['Byte Materials', 'Byte Solutions', 'Byte Analytics']"`.

**Attempt 2** — Challenge `0xd51179bf...`
- **Error**: `"No candidates produced a score for question 1"`
- **Root cause**: Complete extraction failure. All 30 companies in `companies.json` had every field null — `ceo_first: null`, `hq_city: null`, `de_ratio: null`, etc. The parser produced structurally valid output with no actual data.
- **Evidence**: The extraction parser likely encountered a document format variant it couldn't handle (a third format beyond financial dossier and regulatory filings), producing empty shells.

**Attempt 3** — No challenge ID
- **Error**: `"GET .../v1/challenge failed after retries"`
- **Root cause**: Network/API failure after the previous failures. The coordinator may have rate-limited the miner address.

### Batch 2: `batch-20260310-0558` — Two Failures

**Attempt 1** — Challenge `0xa0d5215d...`
- **Error**: `"Unsupported challenge document format for rule-based extraction"`
- **Root cause**: The challenge document didn't contain either "leadership dossiers" or "consolidated regulatory filings" in its text, so `extract_rule_based_companies` (`solver.py:1653-1658`) raised an error. A third document format was encountered that the parser didn't support.

**Attempt 2** — Challenge `0x2a44c90f...`
- **Error**: Same — `"Unsupported challenge document format for rule-based extraction"`
- **Root cause**: Same as attempt 1. The coordinator served the same document format that the parser couldn't handle.

### The Successful Solve

After these 5 failures, the system was eventually run against a challenge (`0x651aef8e...`) that used the financial dossier format. The rule-based parser successfully extracted all 25 companies, the computation pipeline answered all 10 questions correctly, the artifact passed all 9 constraints, and the on-chain receipt was posted (tx: `0x877160a7...`).

### Failure Mapping Table

| # | BOTCOIN Failure | Root Cause | OfficeQA Equivalent | Recommended Mitigation |
|---|----------------|------------|---------------------|----------------------|
| 1 | Ambiguous alias resolution ("Byte" → 3 candidates) | Short aliases map to multiple companies; data left unassigned | Column header ambiguity in Treasury tables (e.g., "Receipts" appearing in multiple table sections) | Require the agent to enumerate all possible interpretations and select the one consistent with surrounding data. Include disambiguation heuristics in the prompt. |
| 2 | Complete extraction failure (all fields null) | Unknown document format; parser produced empty shells | OCR/parsing failure on pre-1996 scanned PDFs producing garbled text | Implement fallback: if structured extraction yields >50% null fields, retry with LLM-based extraction. Include "extraction confidence" scoring. |
| 3 | Unsupported document format | Hardcoded format detection failed | Table layout variants across 86 years of bulletins (different header structures, merged cells, landscape vs portrait) | Don't hardcode format detection. Use LLM to classify table structure first, then apply format-specific extraction rules. |
| 4 | "No candidates matched" (empty filter result) | Filters depended on data that wasn't extracted | Question references a value from a table that the parser couldn't read | Validate extraction completeness BEFORE attempting computation. If critical fields are missing, flag and attempt re-extraction. |
| 5 | Network/API failure after repeated errors | Rate limiting or transient failure | API timeout during competition (unlikely but possible) | Implement retry with exponential backoff (already present in solver.py). Cache intermediate results. |
| 6 | Qualifier misinterpretation ("just under X" → X instead of X-1) | Initial LLM-only approach didn't apply deterministic rules | Unit confusion ("in millions" vs "in thousands") or fiscal year vs calendar year | Hardcode all known unit/qualifier rules. Include explicit unit normalization step. Never let the LLM do arithmetic on raw extracted values. |
| 7 | Near-tie cascade (wrong answer on Q4 breaks constraints C3 and C7) | Single numeric proximity error propagated | Small extraction error in one data point pushes regression result beyond 1% tolerance | Generate alternate candidates for close values. Validate downstream computations for sensitivity to input perturbations. |

---

## Section 6: Prompt Patterns and LLM Instructions

### Extraction Prompt (LLM Path)

```python
# solver.py:727-744
prompt = f"""
You are extracting structured company data for a deterministic BOTCOIN solver.

Rules:
- Output JSON only.
- Use the exact company names from the provided companies array as canonical_name.
- Preserve raw number phrases exactly in employees_raw and revenue_millions_raw.
- Do not round. Do not reinterpret qualifiers in the JSON.
- If a field is missing, return null.
- metadata may include extra scalar fields that are clearly stated in the document.

Companies:
{json.dumps(challenge.companies, indent=2)}

Document:
{challenge.doc}
"""
```

**System message**: `"Extract structured company data exactly and conservatively."`

**What works**: The instruction to "preserve raw number phrases exactly" and "do not round" is critical — it defers numeric interpretation to deterministic code. The instruction to return null for missing fields prevents hallucination.

**What fails**: The prompt doesn't give examples of what "raw number phrases" look like, doesn't specify how to handle conflicting data (a company mentioned with different employee counts in different paragraphs), and doesn't address alias confusion.

### Planning Prompt (LLM Path)

```python
# solver.py:771-796
prompt = f"""
Compile this BOTCOIN challenge into a deterministic execution plan.

Requirements:
- Output JSON only.
- question_plans must be executable without further language interpretation.
- Use only fields that exist in the extracted company records.
- Use strategy=rank for company-selection questions.
- For metric.kind use one of: field, ratio, arithmetic.
- For filters use ops: eq, neq, contains, startswith, in.
"""
```

**System message**: `"Compile natural language BOTCOIN questions into a deterministic JSON plan."`

**What works**: The constraint that plans be "executable without further language interpretation" is the key insight — it forces the LLM to translate ambiguous natural language into unambiguous operations.

**What fails**: The enum of allowed metric kinds and filter ops is limited. If a question requires a computation not in the allowed set (e.g., standard deviation), the plan can't express it.

### Artifact Output Instruction (from skill.md)

```
Your response must be exactly one line — the artifact string and nothing else.
Do NOT output "Q1:", "Looking at", "Let me", "First", "Answer:", or any reasoning.
Do NOT explain your process. Output ONLY the single-line artifact that satisfies
all constraints. No preamble. No JSON. Just the artifact.
```

**What works**: Aggressively suppressing reasoning output and preamble. This is a well-known prompt engineering pattern for getting clean structured output.

### Effective Prompt Fragments Adaptable for OfficeQA

1. **"Preserve raw values, do not interpret"** → For Treasury extraction: "Extract the exact numeric string as it appears in the table cell, including any unit indicators (M, B, thousands). Do not convert units. Store the raw string and the unit separately."

2. **"If a field is missing, return null"** → "If a value cannot be confidently read from the table, return null rather than guessing. A null that triggers a re-read is better than a wrong number that cascades."

3. **"Executable without further language interpretation"** → For OfficeQA computation planning: "Express your computation as a sequence of operations (filter, sort, divide, sum, regress) with explicit column references and row selectors. Each step must be mechanically executable."

---

## Section 7: Transferable Patterns — Concrete Recommendations

### For the Jinja2 Prompt Template (`prompts/officeqa_prompt.j2`)

The prompt should encode a three-phase methodology mirroring the BOTCOIN architecture:

**Phase 1 — Extraction Instructions:**

```
EXTRACTION RULES:
1. Read each table cell exactly as printed. Do not convert units, round, or interpret.
2. Record the unit indicator separately: "millions of dollars", "thousands", "percent", "ratio".
3. For each extracted value, note the source: PDF name, page number, table title, row header, column header.
4. Handle these specific patterns:
   - "n.a." or "---" or "(X)" → null (not zero)
   - Parentheses around numbers → negative value
   - "r" or "p" superscripts → "revised" or "preliminary" flags
   - Fiscal year references (e.g., "fiscal year ending June 30") → convert to calendar year range
5. When a table has hierarchical headers (merged cells spanning columns), resolve each data cell
   to its full column path: e.g., "Public Debt > Interest-bearing > Marketable > Bills"
6. If a value appears ambiguous or you cannot confidently extract it, output null and flag it
   for re-extraction rather than guessing.
```

**Phase 2 — Computation Instructions:**

```
COMPUTATION RULES:
1. After extraction, perform all computations in code, not in your head.
2. For ratios: divide numerator by denominator. Do not approximate.
3. For growth rates: (new - old) / old * 100. Verify the sign.
4. For regressions: use scipy.stats.linregress or equivalent. Report slope, intercept, r-squared.
5. For multi-year aggregations: sum individual years. Do not estimate from averages.
6. Always verify unit consistency before computing: if one value is in millions and another
   in thousands, convert before operating.
7. Round only at the final answer step, not during intermediate computations.
```

**Phase 3 — Validation Instructions:**

```
VALIDATION RULES:
1. Before submitting, verify:
   - The answer's unit matches what the question asks for
   - The answer is within a plausible range (e.g., a percentage between -100 and +10000)
   - If the question asks about a specific year, your data is from that year
   - If fiscal year vs calendar year matters, you used the correct one
2. If you computed a derived value (ratio, growth rate), recompute it from scratch
   using the raw extracted values to verify.
3. If your answer depends on multiple extracted values, check that none are null.
   A partial computation is worse than admitting uncertainty.
```

### For Skills Files (`skills/`)

**Skill 1: `known_pitfalls.md` — Treasury Bulletin Parsing Pitfalls**

Outline:
- **Unit confusion matrix**: Table of all unit indicators found in Treasury Bulletins (millions, thousands, billions, percent, basis points) with conversion factors
- **Fiscal year calendar**: U.S. government fiscal year runs October 1 to September 30. FY2024 starts October 1, 2023.
- **Table header patterns**: Common hierarchical header structures in Treasury Bulletins with examples
- **Revision markers**: How "revised" and "preliminary" data differ and which to prefer
- **Historical format changes**: Pre-1996 scanned PDFs vs post-1996 born-digital. OCR artifacts to watch for.
- **Common false cognates**: Column headers that look similar but mean different things across different tables (e.g., "Receipts" in revenue tables vs. Treasury receipt instruments)

**Skill 2: `computation_patterns.md` — Worked Examples**

Outline:
- **Linear regression example**: Given 9 annual data points, compute slope using least-squares. Show the exact formula and a worked numeric example.
- **T-test example**: Given two sets of values, compute the t-statistic. Show the formula with degrees of freedom.
- **Growth rate calculation**: Show (new-old)/old with explicit handling of negative base values and zero values.
- **Multi-step computation**: "What was the ratio of 2024 marketable debt to 2020 marketable debt?" → Extract both values → verify units → divide → round to appropriate precision.
- **Temporal aggregation**: "What was the average annual growth rate from 2015 to 2023?" → Extract 9 values → compute 8 year-over-year rates → average.

**Skill 3: `table_parsing_guide.md` — Table Structure Recognition**

Outline:
- **Header hierarchy resolution**: When a column header spans 3 sub-columns, how to map each data cell to its full header path
- **Row header indentation**: Indented row headers indicate subcategories. The parent row is often a sum of children.
- **Footnote resolution**: How to find and apply footnotes that modify values (e.g., "1 Includes xyz" or "2 Excludes abc")
- **Multi-page tables**: Tables that span pages — how to detect continuation and merge
- **Landscape tables**: Tables rotated 90 degrees in the PDF — parsing strategy

### For Validation Strategy

Based on the BOTCOIN validation patterns and failures:

1. **Extraction completeness check**: After extracting all values needed for a question, verify that none are null. If any are null, attempt re-extraction from a different part of the document or a different parsing strategy before computing. This directly mirrors the BOTCOIN pattern where missing `satisfaction_rating` caused "no candidates matched."

2. **Unit consistency check**: Before any computation, verify that all operands are in the same unit. This is the OfficeQA equivalent of the qualifier handling in BOTCOIN.

3. **Plausibility bounds**: After computing an answer, check it against reasonable bounds. A percentage above 10,000% or a dollar amount that's negative when it shouldn't be indicates an extraction or computation error.

4. **Sensitivity analysis for close values**: When two candidate answers are within 5% of each other, flag the result and attempt to verify by re-reading the source data. This mirrors the near-tie detection pattern.

5. **Recomputation verification**: For any derived value, recompute from raw extracted numbers as a cross-check. This is the BOTCOIN pattern of `validate_dossier_artifact` recomputing prime numbers and equations independently.

---

## Section 8: What Does NOT Transfer

### Synthetic vs. Real Document Structure

The BOTCOIN challenges use synthetic documents with predictable, template-generated formats. The entire regex extraction engine (`DOSSIER_FORMAL_LEADER_RE`, `DOSSIER_RUNS_LEADER_RE`, etc.) is built around exact syntactic patterns that the coordinator generates. Real Treasury Bulletins have no such regularity — table formats evolved over 86 years, column headers are inconsistent between issues, and scanned documents introduce OCR noise. The regex-based extraction approach is entirely non-transferable to OfficeQA. The only transferable extraction strategy is the LLM-based path with structured output.

### Fixed Entity Set

BOTCOIN provides the exact list of 25 company names upfront in the `companies` array. The solver can match extracted data against this known set. OfficeQA has no equivalent — the agent must discover which tables and rows are relevant to each question without a predefined entity list. This makes extraction significantly harder because the agent must navigate a 89,000-page corpus to find the right 2-3 pages.

### Deterministic Constraint Satisfaction

The artifact construction phase (acrostics, prime numbers, banned letters, exact word counts) is entirely specific to BOTCOIN's challenge format. None of this transfers to OfficeQA, which requires a single numeric or short-text answer.

### Simple Metric Functions

The question metrics in BOTCOIN are straightforward: max, min, ratio, sum. OfficeQA requires statistical operations (linear regression, t-tests, correlation coefficients) that the solver doesn't implement. The `evaluate_expression` framework is a good starting point but needs significant extension.

### Alias Resolution Complexity

The multi-pass alias resolution algorithm is tailored to BOTCOIN's specific problem of short aliases (2-letter ticker symbols, first-word natural names). Treasury Bulletins don't have this problem — entities are identified by explicit table titles and row headers, not ambiguous short names. However, the *principle* of multi-pass resolution (try to match, defer if ambiguous, retry with more context) is transferable to situations where the same metric appears in multiple tables under different names.

### Single-Document Scope

Each BOTCOIN challenge is self-contained: one document, all data present. OfficeQA requires cross-document reasoning — a question might reference data from two different bulletin issues separated by years. The BOTCOIN pipeline has no mechanism for multi-document retrieval, relevance ranking, or temporal alignment across documents.

### Hardcoded Fallbacks

Lines 1319-1328 of `solver.py` contain hardcoded alias-to-company mappings (`"AC" → "Aero Corp"`, `"NS" → "Neos Solutions"`). These are specific to challenges the developer encountered and would break on any other challenge with different companies. This is an anti-pattern — a brittle fix that works for exactly one scenario. For OfficeQA, every disambiguation must be principled and generalizable.

### The 1% Tolerance Gap

BOTCOIN's verifier is binary: pass or fail, with exact match required. OfficeQA uses 1% fuzzy matching. This means OfficeQA is actually more forgiving on individual values but less forgiving on precision — a value that's off by 2% still fails, whereas in BOTCOIN the same error would fail too but the cascading effects would be different. The validation strategy needs to account for this tolerance band: verify that extracted values are within 1% of the true value, not just "close enough to seem right."

---

## Summary

The BOTCOIN codebase demonstrates a mature response to the fundamental challenge of AI-assisted document QA: **use the LLM for language understanding, use code for computation, and validate everything before submitting**. The three-phase architecture (extract → compute → validate) and the hard LLM/code boundary are directly transferable to OfficeQA. The specific extraction regexes, constraint satisfaction logic, and synthetic document assumptions are not. The most valuable lessons are the failure modes: qualifier misinterpretation, incomplete extraction, format inflexibility, and cascading errors from a single wrong value. Building defenses against these specific failure modes into the Arena prompt and skills files is the highest-leverage use of this audit.
