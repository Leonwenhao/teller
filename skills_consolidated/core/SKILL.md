# OfficeQA Agent

## IRON RULES — violate these and you score ZERO

1. **WRITE /app/answer.txt in EVERY Python block.** A rough answer beats an empty file. Every Python block MUST end with: `with open('/app/answer.txt','w') as f: f.write(str(result))`. This is non-negotiable.
2. **ALL math in Python.** Use scipy.stats, numpy, or statsmodels. Never compute in natural language. Never implement a named formula from memory — check the Named Formulas section below first.
3. **After writing your final answer, FINISH IMMEDIATELY.** Do not re-read answer.txt. Do not re-verify your extraction. Do not second-guess. Only reopen a file if you found a concrete unit, date, or cell-path error. Overwriting a correct answer with a "verification" is the #1 cause of wrong answers.

## WORKFLOW

1. **Read question.** Identify: exact metric, time period, requested units, how many values needed, whether it says "reported IN" a specific bulletin.
2. **Classify:**
   - "reported IN [month year]" → open THAT exact file only
   - Single value from one period → simple lookup
   - Multiple values across years → check for retrospective table FIRST (see Retrieval below)
   - Named formula (regression, Theil, Gini, etc.) → check Named Formulas below
   - External knowledge (country groups, historical events) → web search first
3. **Retrieve.** Use grep. Never scroll. `grep -l "metric" /app/corpus/treasury_bulletin_YYYY_*.txt`, then `grep -n -i "metric" FILE.txt`, then `sed -n 'START,ENDp' FILE.txt`.
4. **Extract.** Check units in table title/header/footnotes. Trace full column path for hierarchical headers. Verify fiscal vs calendar year.
5. **Compute.** Python only. Write answer.txt in every code block.
6. **Format.** Write ONLY the bare number. No units, no labels, no %, no $, no explanation.

## RETRIEVAL STRATEGY

**For multi-year questions (the biggest failure pattern):**
1. ALWAYS search the LATEST year in the range FIRST for a retrospective summary table. Example: "values from 1969-1980" → `grep -n "your metric" /app/corpus/treasury_bulletin_1981_*.txt /app/corpus/treasury_bulletin_1982_*.txt`. One retrospective table is 10x faster and more accurate than opening 12 files.
2. If no retrospective table, batch grep: `grep -h "metric" /app/corpus/treasury_bulletin_196*.txt /app/corpus/treasury_bulletin_197*.txt`
3. Track what you have: `needed = list(range(1969, 1981)); found = {}; missing = [y for y in needed if y not in found]`
4. NEVER compute until `len(found) == len(needed)`. A missing value = wrong answer.

**General retrieval:**
- Data for year X often appears in bulletins from X+1 or X+2
- Try synonyms: "outlays"↔"expenditures", "receipts"↔"revenue", "defense"↔"military"
- After ~10 failed searches, completely change strategy — different terms, different years, different table type
- `head -60 FILE.txt` shows the table of contents

## UNIT CONVERSION — #1 Error Pattern

Treasury tables show values in "thousands of dollars" or "millions of dollars" (check table title, header rows, column headers, AND footnotes — all four places).

- Question says "nominal dollars" / "in dollars" = raw unconverted:
  - Table in thousands → MULTIPLY by 1,000
  - Table in millions → MULTIPLY by 1,000,000
- Question says "in millions" + table in millions → no conversion
- Question says "in millions" + table in thousands → DIVIDE by 1,000
- Question says "in billions" + table in millions → DIVIDE by 1,000
- Parenthetical values (234) = NEGATIVE, not footnote
- "n.a." or "---" = not available, NOT zero
- When question doesn't specify units, use table's units

## FISCAL YEAR vs CALENDAR YEAR

- Before 1976: FY = July 1 – June 30. FY1975 = Jul 1974 – Jun 1975
- Transition quarter: Jul 1 – Sep 30, 1976
- After 1976: FY = October 1 – September 30. FY2024 = Oct 2023 – Sep 2024
- "Calendar year 1981" ≠ "fiscal year 1981" — different months. When question says CY, you may need to sum individual months.

## NAMED FORMULAS — Always use these exact definitions

**Regression:** `from scipy.stats import linregress; slope, intercept, _, _, _ = linregress(x, y); prediction = slope * target + intercept`
**T-statistic:** `from scipy.stats import ttest_ind; t, p = ttest_ind(a, b)`
**Theil index:** `theil = np.mean((values / np.mean(values)) * np.log(values / np.mean(values)))`
**CAGR:** `((end / start) ** (1 / n_years) - 1) * 100`
**YoY growth:** `((new - old) / old) * 100`
**Continuously compounded growth:** `np.log(V_end / V_start) / n_years`
**Symmetric / Fisher growth rate:** `2 * (V2 - V1) / (V2 + V1)` or `(V2 - V1) / np.sqrt(V1 * V2)`
**Expected Shortfall (CVaR) at α%:** `np.mean(sorted(returns)[:int(len(returns) * alpha)])`
**Arc elasticity:** `((Q2-Q1)/((Q2+Q1)/2)) / ((P2-P1)/((P2+P1)/2))`
**HHI:** `sum(s**2 for s in shares)` where shares are decimals. Effective N = `1/HHI`
**Gini (2 values):** `abs(x1 - x2) / (x1 + x2)`
**Coefficient of variation:** `np.std(values, ddof=0) / np.mean(values)`
**Hazard rate:** `-np.log(V2 / V1) / t`
**Winsorized range:** Sort, replace bottom/top k with boundary values, range = max - min
**Box-Cox:** `(x**lam - 1) / lam` if lam ≠ 0; `np.log(x)` if lam = 0
**Std dev — population:** `np.std(values, ddof=0)` — use when question says "population"
**Std dev — sample:** `np.std(values, ddof=1)` — use when question says "sample"
**HP filter:** `import statsmodels.api as sm; cycle, trend = sm.tsa.filters.hpfilter(series, lamb=1600)`
**ARIMA:** `from statsmodels.tsa.arima.model import ARIMA; model = ARIMA(series, order=(p,d,q)).fit()`
**Polynomial regression degree k:** `np.polyfit(x, y, k)` returns coefficients highest-degree first
**Percentage point change:** `new_pct - old_pct` (NOT percent change)
**Percent change:** `((new - old) / old) * 100`

## DOMAIN TRAPS

**"Reported in" vs "Reported for":**
- "reported IN February 1938" → MUST open treasury_bulletin_1938_02.txt
- "reported FOR February 1938" → any bulletin covering that period
- "reported in Feb 1938 AND Jan 1939" → open BOTH files, get each value from its own file
- NEVER substitute a retrospective table for a "reported in [date]" question

**Financial statement terms:**
- "Capital" / "Paid-in capital" = original appropriation (fixed round number, e.g. $200M)
- "Total capital" / "Fund balance" / "Net position" = capital + accumulated earnings (e.g. $8B)
- If question says "capital" without "paid-in", use the TOTAL figure (bottom-line equity)
- "Net receipts" = total minus refunds. "Net outlays" = outlays minus offsetting receipts
- "Gross debt" includes intragovernmental holdings. "Debt held by public" excludes them
- "Interest on public debt" ≠ "interest credited to government accounts" — different line items

**False cognates:**
- "Receipts" (revenue) vs Treasury receipt instruments (securities)
- "Expenditures" vs "Outlays" — may differ in scope
- "Budget surplus/deficit" vs "Operating cash balance" — different concepts

**Document versioning:** Same data can differ across bulletin issues. If question does NOT say "reported in," check 1-2 later bulletins — use the later (revised) value.

**Table hierarchies:** Hierarchical headers are flattened as "Parent - Child - Grandchild" in the parsed files. Always trace the FULL column path. Row indentation means subcategories; parent row = total of children.

**Pre-1996 OCR:** Letters and digits can be confused (l↔1, O↔0), commas dropped, columns shifted. Cross-reference if a value seems wrong.

## OUTPUT FORMAT

Write ONLY the bare number to /app/answer.txt:
- "percent value (12.34%, not 0.1234)" → write `12.34`
- "rounded to nearest hundredths" → `round(result, 2)`
- "rounded to nearest thousandths" → `round(result, 3)`
- "in billions" and your value is in millions → divide by 1000

```python
formatted = round(result, 2)
with open('/app/answer.txt', 'w') as f:
    f.write(str(formatted))
```

## EXTERNAL DATA

**CPI-U annual averages (BLS, base 1982-84=100):**
1938:14.1, 1940:14.0, 1945:18.0, 1950:24.1, 1955:26.8, 1960:29.6, 1965:31.5, 1970:38.8, 1975:53.8, 1979:72.6, 1980:82.4, 1985:107.6, 1990:130.7, 1995:152.4, 2000:172.2, 2005:195.3, 2010:218.1, 2015:237.0, 2020:258.8
Real dollars: `nominal * (CPI_target_year / CPI_source_year)`

**Historical dates:** WWII ended 1945. Korean War began June 1950. Vietnam: 1955-1975. Gulf War: 1990-1991.

**Web search** for country groups, treaty dates, or definitions not in bulletins:
```python
import urllib.request, json
url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ','_')}"
data = json.loads(urllib.request.urlopen(url, timeout=10).read().decode())
print(data.get('extract',''))
```
