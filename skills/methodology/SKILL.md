# OfficeQA Methodology — Follow This For Every Question

## CRITICAL RULES
1. **WRITE /app/answer.txt IMMEDIATELY after your FIRST extraction.** Do not wait until you've finished all steps. A rough answer scores points; an empty file scores ZERO. Overwrite it with a better answer later if you refine. Every Python block that computes a value MUST end with `with open('/app/answer.txt','w') as f: f.write(str(result))`.
2. ALL arithmetic must be done in Python code. Never compute in natural language. For ANY statistical measure (std dev, kurtosis, z-score, Gini, VaR, median, percentile, polynomial fit, etc.), use `scipy.stats` or `numpy` — they have every function you need. Do not implement formulas from scratch.
3. Use grep/search to find data in documents. NEVER scroll through entire files page by page.
4. DO NOT write a plan or outline before starting. Execute immediately: read question → grep → extract → compute → write answer.
5. Be FAST. Minimize steps: grep → read section → extract → compute → write answer. Do NOT re-read files you already read. Do NOT verify by reading answer.txt back. Aim for 3-5 tool calls total.

## Question Classification (decide BEFORE searching)
- **Exact-bulletin lookup** ("reported IN [month year]"): open THAT specific file, find the value, done.
- **Unanchored lookup** ("in [year]" or "for fiscal year X"): search across bulletins for the period.
- **List / time series** ("for years X through Y", "monthly values"): count exactly how many values needed, extract ALL before computing.
- **Analytic computation** ("predict using regression", "growth rate", "Theil index"): extract data first, then use the correct Python formula.
- **External knowledge** ("gold bloc", "Allied nations"): web search for membership/definition FIRST, then find data.

## Four-Phase Pipeline (Follow IN ORDER)

### Phase 1: Retrieve
Parse the question for: the exact metric, time period (calendar vs fiscal year), units requested, and how many data points needed.

Find documents efficiently:
- Files at `/app/corpus/treasury_bulletin_YYYY_MM.txt`
- `grep -l "search term" /app/corpus/treasury_bulletin_YYYY_*.txt` to find files
- `grep -n -i "search term" /app/corpus/FILE.txt` to find line numbers
- Read ONLY the relevant section: `sed -n '500,650p' FILE.txt`
- Data for year X appears in bulletins from X and X+1

### Phase 2: Extract
- Before extracting, identify the UNIT from: table title, header rows, column headers, footnotes
- For hierarchical column headers, trace the FULL path (e.g., "Public Debt > Interest-bearing > Marketable")
- Verify fiscal year vs calendar year match
- Parenthetical values = NEGATIVE. "n.a." = not available (NOT zero).
- If values look wrong, try a later bulletin for revised figures
- When extracting multiple values (a list, time series): COUNT exactly how many the question requires, extract each with its label, verify count matches before computing. A missing value cascades into a wrong answer.

### Phase 3: Compute
Write Python code for ALL calculations. **ALWAYS write to /app/answer.txt at the end of EVERY Python block** — even partial results:
```python
print(f"Extracted: {values}")
result = ...  # your computation
print(f"Answer: {result}")
# ALWAYS write answer — do this in EVERY code block, not just the last one
with open('/app/answer.txt', 'w') as f:
    f.write(str(result))
```

### Phase 4: Validate (mental check, no extra tool calls)
1. Unit matches question? 2. Answer plausible? 3. Correct time period? 4. No null values? 5. Re-read question — did you answer what was asked?

## Phase 5: Format the Answer

Before writing to /app/answer.txt, re-read the question's format instructions CAREFULLY.

FORMATTING RULES:
- If the question says "reported as a percent value (12.34%, not 0.1234)" → write the number as 12.34, NOT 0.1234
- If the question says "rounded to the nearest thousandths place" → round to 3 decimal places (e.g., 0.479)
- If the question says "rounded to the nearest hundredths place" → round to 2 decimal places (e.g., 12.35)
- If the question says "rounded to the nearest tenths place" → round to 1 decimal place (e.g., 27.0)
- If the question says "in billions of dollars" → divide by 1000 if your extracted value is in millions
- If the question says "in millions of dollars" → your value is likely already in millions from the table

CRITICAL: Write ONLY the bare number to /app/answer.txt.
- CORRECT: echo "12.34" > /app/answer.txt
- WRONG: echo "12.34%" > /app/answer.txt
- WRONG: echo "$12.34 billion" > /app/answer.txt
- WRONG: echo "The answer is 12.34" > /app/answer.txt
- WRONG: echo "## Answer\n12.34" > /app/answer.txt

Use Python for the final formatting to avoid mistakes:
```python
result = 12.3456
# If question asks "rounded to nearest hundredths place":
formatted = round(result, 2)  # 12.35
with open('/app/answer.txt', 'w') as f:
    f.write(str(formatted))
```

## When to Search the Web

Some questions reference historical facts, country groupings, economic terms, or events NOT contained in the Treasury Bulletins. Examples: "gold bloc countries," "Axis powers," specific treaty dates, economic definitions.

DECISION RULE: If the question mentions a named group, historical event, or definition that you are not 100% certain about, search the web BEFORE computing your answer:

```python
import urllib.request
import json

def web_lookup(query):
    """Quick web lookup via Wikipedia API."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read().decode())
        return data.get('extract', 'No result found')
    except Exception as e:
        return f"Search failed: {e}"

# Example: verify gold bloc membership
print(web_lookup("Gold bloc"))
```

Do NOT web search for data that should be in the Treasury Bulletins. The corpus has the numbers; the web has the context.
