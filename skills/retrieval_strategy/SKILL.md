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

## DO NOT
- Open a file and scroll page by page — you will run out of steps
- Read the same file more than twice — extract what you need in one pass
- Spend more than 15 steps on retrieval — if you haven't found data by then, change your search strategy
- Forget to write /app/answer.txt — an unwritten answer scores ZERO
