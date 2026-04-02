# Quick Reference — Arena Competition

## Common Commands

```bash
# Submit and check
arena submit                          # Submit current config for scoring
arena status                          # Check latest submission result

# OpenRouter balance check
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | python3 -m json.tool

# Run reward.py locally on a single prediction
python3 -c "
from reward import score_answer
print(score_answer('543.21', '548.0', tolerance=0.01))  # 1% tolerance
"

# Quick question lookup from CSV
python3 -c "
import pandas as pd
df = pd.read_csv('officeqa_full.csv')
q = df[df.uid == 'TARGET_UID']
print(f'Q: {q.question.values[0]}')
print(f'A: {q.answer.values[0]}')
print(f'Source: {q.source_files.values[0]}')
print(f'Difficulty: {q.difficulty.values[0]}')
"

# Count questions by difficulty
python3 -c "
import pandas as pd
df = pd.read_csv('officeqa_full.csv')
print(df.difficulty.value_counts())
"

# Search for questions mentioning a topic
python3 -c "
import pandas as pd
df = pd.read_csv('officeqa_full.csv')
mask = df.question.str.contains('defense', case=False, na=False)
for _, r in df[mask].iterrows():
    print(f'{r.uid}: {r.question[:100]}...')
    print(f'  Answer: {r.answer}, Source: {r.source_files}')
    print()
"
```

## Scoring Math

- Tolerance: 1% (|predicted - truth| / |truth| <= 0.01)
- Example: truth=543, predicted=548 → error=5/543=0.92% → PASS
- Example: truth=543, predicted=555 → error=12/543=2.21% → FAIL
- Example: truth=2.3%, predicted=2.1% → error=0.2/2.3=8.7% → FAIL (small values are strict!)
- Negative: truth=-50, predicted=-50.4 → error=0.4/50=0.8% → PASS
- Sign error: truth=-50, predicted=50 → error=100/50=200% → FAIL

## Budget Math

| Model | Input $/M tok | Output $/M tok | ~Cost/question | Full run cost |
|-------|---------------|----------------|----------------|---------------|
| Claude Haiku 4.5 | $0.80 | $4.00 | ~$0.08 | ~$20 |
| GPT-4.1-mini | $0.40 | $1.60 | ~$0.05 | ~$12 |
| Claude Sonnet 4.5 | $3.00 | $15.00 | ~$0.40 | ~$100 |
| Claude Opus 4.6 | $15.00 | $75.00 | ~$1.50 | ~$370 |

Note: Costs are estimates. Verify at https://openrouter.ai/models

## Fiscal Year Quick Reference

| Period | FY Definition | Example |
|--------|--------------|---------|
| Before 1976 | Jul 1 → Jun 30 | FY1940 = Jul 1939 – Jun 1940 |
| Transition Q | Jul 1 → Sep 30, 1976 | One-time 3-month quarter |
| After 1976 | Oct 1 → Sep 30 | FY2024 = Oct 2023 – Sep 2024 |

## Daily Checklist

- [ ] What's the current score? (check SCRATCHPAD.md)
- [ ] What failure pattern has highest EV to fix? (check failure_catalog.md)
- [ ] How much OpenRouter credit remains? (check balance)
- [ ] Did any regressions appear from last iteration? (compare question-by-question)
- [ ] Updated SCRATCHPAD.md at end of session?
