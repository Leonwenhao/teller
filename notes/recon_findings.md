# Reconnaissance Findings — Day 1-2

> Fill this in immediately after running `arena init`. Every answer here shapes the rest of the competition.

---

## Arena Environment

**arena.yaml structure:**
```yaml
# Paste the full generated arena.yaml here, then annotate each field
```

**Jinja2 template variables:**
What variables does the prompt template receive? (question text, metadata, file paths, etc.)

**Document corpus format:**
- [ ] Raw PDFs only
- [ ] Parsed JSON available
- [ ] Transformed TXT available
- [ ] Other: ___

**Document corpus location:**
Path in the agent's filesystem: ___

**Can I inject pre-parsed files?**
- [ ] Yes, via skills/ directory
- [ ] Yes, via MCP server
- [ ] Yes, via filesystem mount
- [ ] No, locked to provided format

**Agent sandbox details:**
- Available tools: ___
- Pre-installed packages: ___
- Filesystem access scope: ___
- Internet access: [ ] yes [ ] no
- Timeout per question: ___
- Max tool calls: ___

## Scoring

**Scoring mechanism:**
- [ ] Purely accuracy on 246 questions
- [ ] Accuracy + reasoning trace quality
- [ ] Accuracy + cost
- [ ] Accuracy + latency
- [ ] Other: ___

**Per-question results visible?**
- [ ] Yes, full breakdown
- [ ] Only aggregate score
- [ ] Partial (easy/hard split)

**Submission limits:**
- Rate limit: ___
- Max submissions per day: ___
- Max total submissions: ___

## Models Available

**Confirmed available on OpenRouter in Arena:**
- [ ] anthropic/claude-opus-4-6
- [ ] anthropic/claude-sonnet-4-5
- [ ] anthropic/claude-haiku-4-5
- [ ] openai/gpt-5.3
- [ ] openai/gpt-5.4
- [ ] openai/gpt-4.1-mini
- [ ] Other: ___

## Baseline Run

**Date:** ___
**Config:** Default from arena init
**Model:** ___
**Score:** ___% (___/246)
**Easy:** ___/113
**Hard:** ___/133
**Cost:** $___
**Time:** ___ minutes

## Key Findings That Change Strategy

(Record anything surprising that requires adjusting the plan from GENESIS.md)

1. ___
2. ___
3. ___
