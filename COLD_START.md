# Cold Start Prompt for Claude Code

> **Paste this entire block when starting a new Claude Code session.**

---

## Who I Am

I'm Leon (柳文浩), founder of Dolores Research. I'm competing in Sentient Arena Cohort 0 — a two-week AI agent competition (March 22 – April 5, 2026) where I configure an OpenHands coding agent to score as high as possible on the OfficeQA benchmark (246 questions over 89,000 pages of U.S. Treasury Bulletins). Backers include Founders Fund, Pantera, Franklin Templeton.

## How to Orient Yourself

1. **Read CLAUDE.md first** — it has my persistent instructions, the competition context, the four-phase pipeline methodology, and the project file structure.
2. **Read SCRATCHPAD.md second** — it has the current state: what day we're on, current best score, what was done last session, what to do next, open questions, budget tracking.
3. **Don't read GENESIS.md or BOTCOIN_AUDIT.md** unless you need deep background on the benchmark or my prior architecture work. They're reference docs, not operational docs.

## What You Should Do

After reading CLAUDE.md and SCRATCHPAD.md, tell me:
- What day/phase we're in
- What the SCRATCHPAD says to do next
- Any concerns or blockers you see

Then we pick up where we left off.

## Critical Rules

- Always update SCRATCHPAD.md at the end of the session with: what we did, current score, next actions, any new decisions, budget spend.
- Never do arithmetic in natural language when working on the agent — that's the core BOTCOIN lesson. Always write Python.
- Track every submission in the iteration tracker table in SCRATCHPAD.md.
- Be budget-conscious with OpenRouter credits ($100 total). Use cheap models for iteration, frontier for final runs.
