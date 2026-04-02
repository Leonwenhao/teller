# Table Parsing Guide — U.S. Treasury Bulletins

> Reference file for navigating the complex table structures found in Treasury Bulletin documents.

## Document Structure

Each Treasury Bulletin is 100-200 pages organized into sections. The table of contents (usually pages 1-3) lists all tables with their page numbers. Tables are grouped by topic: receipts and expenditures, public debt, cash operations, federal securities, tax collections, etc.

When looking for data, start by identifying the section most likely to contain it. For example, "total expenditures for national defense" would be in the expenditures section, not the debt section.

## Table Anatomy

A typical Treasury Bulletin table has these components (top to bottom):

1. **Table title** — describes what the table contains. Often includes the unit indicator ("In millions of dollars") and the time period coverage.
2. **Column header row(s)** — may be 1-3 rows deep. Parent headers span multiple sub-columns. Read from top to bottom to build the full column path.
3. **Data rows** — the actual values. Row headers on the left describe what each row measures. Indentation indicates subcategories.
4. **Total rows** — rows labeled "Total" or with bold/underline are sums of the rows above them.
5. **Footnotes** — appear at the bottom of the table. Referenced by superscript numbers in the data. Footnotes can modify values ("includes X" or "excludes Y") and MUST be read.

## Reading Hierarchical Column Headers

Example of a three-level header structure:

```
|                    | Public Debt Securities                                    |
|                    | Interest-bearing              | Non-interest-bearing      |
|                    | Marketable | Non-marketable  | Matured  | Other          |
|--------------------|------------|-----------------|----------|----------------|
| Outstanding start  | 1,234      | 5,678           | 90       | 12             |
| Issued during      | 456        | 789             | 0        | 3              |
```

To read the value "1,234" correctly, trace both paths:
- Column path: Public Debt Securities → Interest-bearing → Marketable
- Row: Outstanding start

The value means: "Marketable interest-bearing public debt securities outstanding at start of period: $1,234"

If you read this value as just "Public Debt Securities: 1,234" you've made a critical error — that's a subcategory, not the total.

## Reading Hierarchical Row Headers

Row indentation shows parent-child relationships:

```
| Category                          | Amount |
|-----------------------------------|--------|
| Total receipts                    | 10,000 |
|   Individual income taxes         | 5,000  |
|   Corporation income taxes        | 2,000  |
|   Social insurance contributions  | 2,500  |
|   Other                           | 500    |
```

The indented rows sum to the parent. "Total receipts" (10,000) = sum of its children (5,000 + 2,000 + 2,500 + 500). If the question asks for "total receipts," use 10,000. If it asks for "individual income taxes," use 5,000.

## Multi-Page Tables

Tables often span multiple pages. When a table continues on the next page, it typically:
- Repeats the column headers at the top of each new page
- May or may not repeat the table title
- The continuation page sometimes says "(Continued)" in the header

When extracting data from a multi-page table, make sure you're reading the correct continuation page, not a different table with similar headers.

## Time Period Columns

Treasury tables present data in time-indexed columns. Common patterns:

- **Monthly columns**: Jan, Feb, Mar, ... Dec within a single fiscal year
- **Quarterly columns**: Q1 (Oct-Dec), Q2 (Jan-Mar), Q3 (Apr-Jun), Q4 (Jul-Sep) — for fiscal year
- **Annual columns**: Multiple years side by side (e.g., 2018, 2019, 2020)
- **Cumulative columns**: "Year to date" or "12 months ending"

Always verify which time period each column represents. A column labeled "1940" could mean calendar year 1940, fiscal year 1940, or the quarter/month ending in 1940 depending on context.

## Markdown Table Representation

In the parsed TXT files, tables are converted to Markdown format. A hierarchical header becomes:

```markdown
| | Public Debt Securities - Interest-bearing - Marketable | Public Debt Securities - Interest-bearing - Non-marketable | ...
```

The hierarchy is flattened into dash-separated paths. When you see a column header like "Public Debt Securities - Interest-bearing - Marketable," read each segment as a level of the original hierarchy.

Be aware that this flattening can introduce ambiguity when different branches of the hierarchy share names. Always use the full column path, not just the leaf name.

## What To Do When the Table Is Unclear

If you cannot confidently determine which cell a question is asking about:

1. Read the full table title for context about what the table covers
2. Read all footnotes — they often clarify ambiguous entries
3. Check if the same data appears in a different table or a later bulletin with clearer formatting
4. Cross-reference: if the question asks about a value that should be a component of a known total, check whether your extracted value plus other components equals the total
5. If still uncertain, flag the extraction as low-confidence and try an alternative document

---

*Update this file when new table structure patterns are discovered during the competition.*
