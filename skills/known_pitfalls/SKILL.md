# Known Pitfalls — Treasury Bulletin Document QA

> This file is read by the agent as context. Every entry here prevents a specific failure mode. Keep entries dense and actionable.

## Unit Conversion — "In Nominal Dollars" and "In Dollars"

THIS IS THE MOST COMMON ERROR PATTERN. Treasury Bulletin tables almost always show values "in thousands of dollars" or "in millions of dollars" (stated in the table title or header row). Questions may ask for the answer in DIFFERENT units.

CRITICAL RULES:
1. ALWAYS check the table's unit indicator (in the title, subtitle, or column header) BEFORE extracting any number
2. If the question asks for "nominal dollars," "in dollars," or "in actual dollars" — it means raw, unconverted dollars
   - If the table shows "in thousands": MULTIPLY your extracted value by 1,000
   - If the table shows "in millions": MULTIPLY your extracted value by 1,000,000
   - If the table shows "in billions": MULTIPLY your extracted value by 1,000,000,000
3. If the question asks for "in millions of dollars" and the table is ALSO in millions — no conversion needed
4. If the question asks for "in millions" but the table is in thousands — DIVIDE by 1,000
5. ALWAYS state the conversion explicitly in your code:

```python
# Example: table shows values "in thousands of dollars"
raw_table_value = 35028267.33  # This is in thousands
# Question asks for "nominal dollars" = raw dollars
answer = raw_table_value * 1000  # Convert thousands to dollars
# answer = 35028267330.0
```

If you are unsure of the table's units, grep the file for "thousands" or "millions" near the table title:
```bash
grep -i "thousand\|million\|billion" treasury_bulletin_YYYY_MM.txt | head -20
```

## Unit Indicators

Treasury Bulletin values appear in different units across tables and eras. The unit indicator can appear in four places: the table title, a header row above the column headers, within the column header itself, or in a footnote. Always check all four locations before assuming a unit. Common units and their conversions:

- "In millions of dollars" → value as-is represents millions
- "In thousands of dollars" → divide by 1,000 to convert to millions
- "In billions of dollars" → multiply by 1,000 to convert to millions
- Bare numbers with no unit indicator → check the table title and any footnotes
- Parenthetical values like (234) → this means negative 234, not a footnote reference
- "n.a." or "---" → null/not available, NOT zero
- Superscript numbers (¹, ², ³) → footnote references, check bottom of table

When a question asks for a value "in millions of dollars" and the table shows values "in thousands," you must convert. When the question doesn't specify units, use the unit from the table and note it in your answer.

## Fiscal Year vs Calendar Year

The U.S. federal fiscal year does NOT align with the calendar year. Critical dates:

- Before 1976: Fiscal year ran July 1 to June 30. FY1975 = July 1, 1974 – June 30, 1975.
- Transition quarter: July 1 – September 30, 1976 (a 3-month "transition quarter" when the U.S. switched fiscal year definitions).
- After 1976: Fiscal year runs October 1 to September 30. FY2024 = October 1, 2023 – September 30, 2024.

When a question asks about "calendar year 1940" but the table shows "fiscal year 1940," these are DIFFERENT time periods. You may need to sum monthly values to construct the calendar year total. Always verify which time period the question uses and which the table uses.

## Document Versioning — Revised Data

Treasury Bulletins frequently revise figures from earlier periods. The same data point can have different values in different bulletin issues.

WHEN YOU FIND A VALUE:
1. Note which bulletin you found it in (e.g., treasury_bulletin_1941_01.txt)
2. If the question asks about data "reported in" a specific bulletin, use THAT bulletin's value only
3. If the question does NOT specify a bulletin, check the next 1-2 bulletins for the same table:
   grep -l "EXACT TABLE TITLE" treasury_bulletin_1941_02.txt treasury_bulletin_1941_03.txt
4. If the same metric appears with a different value in a later bulletin, use the LATER value (it is the revision)
5. Differences are typically small (e.g., 21 million on a figure of several billion) but can push you outside the 1% tolerance

This matters most for: public debt totals, expenditure summaries, and any figure from the most recently completed fiscal year (which gets revised as final data comes in).

## Table Header Hierarchies

Treasury Bulletin tables use hierarchical row AND column headers. A data cell's meaning depends on reading both its row header (often indented to show parent-child relationships) and its column header (which may span multiple sub-columns). When extracting a value, trace both the row header path and the column header path to ensure you have the correct cell.

Common pattern: A column header "Public Debt Securities" spans three sub-columns: "Interest-bearing," "Matured," and "Bearing No Interest." Each sub-column may have further sub-divisions. A value in this table only makes sense when you specify the full column path.

Row indentation indicates hierarchy: indented rows are subcategories of the row above. The parent row is often a sum or total of its children. If the question asks for a total, use the parent row. If it asks for a component, use the indented child row.

## Pre-1996 Document Artifacts

Bulletins before 1996 are scans of physical documents. Common OCR artifacts to watch for:

- "l" (lowercase L) misread as "1" (digit one) and vice versa
- "O" (letter O) misread as "0" (digit zero)
- Commas in numbers misread or dropped (1,234 becomes 1234 or 1.234)
- Decimal points misread as commas or absent
- Column alignment errors where values shift to adjacent columns
- Merged or overlapping text in dense table regions

When a value looks implausible, consider OCR error as a possible cause and cross-reference with other data in the same table for consistency.

## Computation Patterns

NEVER compute regressions, t-statistics, growth rates, or any multi-step arithmetic in natural language. Always write Python code using scipy.stats or numpy. A single arithmetic error in a 9-point time series for linear regression pushes the result well beyond 1% tolerance.

For linear regression: use `scipy.stats.linregress(x, y)` which returns slope, intercept, r_value, p_value, and stderr.
For t-statistics: use `scipy.stats.ttest_ind(a, b)` for independent samples or `scipy.stats.ttest_1samp(a, popmean)` for one-sample.
For growth rates: `(new - old) / old * 100`. Verify the sign. Handle zero denominators.

## Common False Cognates

These column headers look similar but mean different things across different tables:

- "Receipts" in a revenue table (money coming in) vs Treasury receipt instruments (securities)
- "Expenditures" (money going out) vs "Outlays" (may or may not include the same items)
- "Gross debt" vs "Debt held by the public" vs "Intragovernmental holdings"
- "Budget surplus/deficit" vs "Operating cash balance"

Always verify that the column header in the table matches the exact term used in the question.

## "Reported in" vs "Reported for" — Date Interpretation

STOP AND READ THIS CAREFULLY. This distinction changes which file you open.

RULE 1: "expenditures reported IN February 1938" → open treasury_bulletin_1938_02.txt and find the summary page total
RULE 2: "expenditures FOR February 1938" → this is the expenditure during February 1938, can be found in any bulletin covering that period
RULE 3: "reported in February 1938 AND January 1939" → open BOTH files separately: treasury_bulletin_1938_02.txt AND treasury_bulletin_1939_01.txt

DO NOT find both values in a single retrospective table from a later bulletin. Each "reported in [date]" value MUST come from THAT specific bulletin file.

This is NOT optional. If the question says "reported in February 1938", you MUST read treasury_bulletin_1938_02.txt. Do not substitute a different bulletin.

## Historical Groupings and External Knowledge

When a question references a named group of countries, organizations, or entities (e.g., "gold bloc countries," "Allied nations," "OPEC members"):
1. First check if the Treasury Bulletin itself lists the members (it sometimes does in table headers or footnotes)
2. If not listed in the bulletin, use web search to verify membership AS OF THE DATE specified in the question
3. Be especially careful about membership dates — countries join and leave groups over time
4. If a borderline member's inclusion/exclusion changes your answer, compute BOTH variants and note the difference

TRAP: Your memorized knowledge about historical groupings may be wrong or imprecise about exact dates. A country you "know" left a group in 1934 might have formally left in 1935. Always verify when the margin matters.

## Financial Statement Terminology

When questions ask about "capital," "total capital," or "net worth" from balance sheet or fund statement:
- "Capital" or "Paid-in capital" = the original amount invested or appropriated (often a fixed, round number)
- "Total capital," "Net position," or "Fund balance" = capital PLUS accumulated earnings, retained profits, valuation gains/losses, and other equity items
- These can differ by orders of magnitude (e.g., $200M paid-in capital vs $8B total fund balance)

RULE: If the question asks about "total" capital or the "capital" of a fund without specifying "paid-in" or "original," it almost certainly means the TOTAL figure (including all accumulated equity), not just the original appropriation. Look for the bottom-line total on the equity/capital section of the balance sheet, not the first "Capital" line item you find.

Additional terms: "Capital stock" = par value of issued shares. "Gold stock" or "Gold certificate account" = monetary gold held by Treasury. "Par value" may differ from market or book value.

Similarly for other financial terms:
- "Total receipts" vs "Net receipts" (net = total minus refunds)
- "Gross debt" vs "Debt held by the public" (gross includes intragovernmental holdings)
- "Expenditures" vs "Net outlays" (outlays = expenditures minus offsetting receipts)

---

*This file grows with each iteration. Every failure that gets resolved becomes a new entry here.*
