# Retrieval Strategy — How to Find Data Efficiently

## MANDATORY: Use grep, not scrolling

Treasury Bulletins are 100-200 pages each. You have limited steps. NEVER open a file and scroll through it.

### Step 1: Find the right file
```bash
# Find which files mention your topic
grep -l "national defense" /app/corpus/treasury_bulletin_1941_*.txt

# If no results, try synonyms or adjacent years
grep -l "defense expenditure" /app/corpus/treasury_bulletin_194*.txt
```

### Step 2: Find the exact section within the file
```bash
# Get line numbers where your topic appears
grep -n -i "national defense" /app/corpus/treasury_bulletin_1941_01.txt

# Show context around a match (20 lines after)
grep -n -i -A 20 "national defense" /app/corpus/treasury_bulletin_1941_01.txt
```

### Step 3: Read ONLY the relevant section
```bash
# Read lines 500-650 (where grep found your table)
sed -n '500,650p' /app/corpus/treasury_bulletin_1941_01.txt
```

### Step 4: When you can't find the data
1. Try synonyms: "outlays"↔"expenditures", "receipts"↔"revenue", "obligations"↔"commitments", "defense"↔"military"
2. Try the next month's bulletin (data publishes 1-3 months after the period)
3. Check the table of contents: `head -60 /app/corpus/treasury_bulletin_1941_01.txt`
4. Try a broader search across all years: `grep -l "your term" /app/corpus/treasury_bulletin_*.txt | head -10`
5. STEP BUDGET: If you haven't found data after ~10 searches, change your search strategy completely — try different terms, different years, or different table types. Do NOT guess.

## Multi-File / Multi-Year Questions

When a question spans many years (e.g., "from 1969 to 1980 inclusive"):

1. **First check for a retrospective table.** A later bulletin often has a historical summary table covering the full range. Search the LATEST year first: `grep -n "your metric" /app/corpus/treasury_bulletin_1981_*.txt` — one table beats 12 separate files.
2. **Batch grep across files.** Extract matching lines from all years in one command: `grep -h "metric name" /app/corpus/treasury_bulletin_196*.txt /app/corpus/treasury_bulletin_197*.txt`
3. **Track extracted values in a Python dict.** After each extraction, check what's still missing:
```python
needed = list(range(1969, 1981))  # 1969-1980 inclusive
found = {1969: 374443, 1970: 381327}  # fill as you go
missing = [y for y in needed if y not in found]
```
4. **Count before computing.** Verify `len(found) == len(needed)` before computing any statistic. A missing value changes the answer.

## DO NOT
- Open a file and scroll page by page — you will run out of steps
- Read the same file more than twice — extract what you need in one pass
- Spend more than 15 steps on retrieval — if you haven't found data by then, change your search strategy
- Forget to write /app/answer.txt — an unwritten answer scores ZERO
