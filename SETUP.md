# SETUP.md — Tool Installation and Configuration

## 1. Arena CLI

The Arena CLI is the primary interface for submitting to the competition and checking scores.

```bash
# Download the CLI (macOS ARM — adjust for your platform)
curl -L https://arena.sentient.xyz/api/download/cli -o arena
chmod +x arena
sudo mv arena /usr/local/bin/arena

# Authenticate (this will open a browser for Sentient Arena sign-in)
arena auth

# Initialize the competition template (creates arena.yaml, prompts/, skills/)
arena init

# After configuring, submit for scoring
arena submit

# Check submission status
arena status
```

**After running `arena init`, immediately inspect:**
- The generated `arena.yaml` — document its full structure in notes/recon_findings.md
- The prompts/ directory — what template files exist? What variables are available?
- The skills/ directory — any pre-populated files?
- The document corpus — what format? Where is it? Raw PDFs or parsed?
- Any README or documentation files Arena provides

## 2. OpenRouter ($100 credit)

OpenRouter provides LLM inference. Your agent routes all model calls through OpenRouter.

```bash
# Sign up / sign in at https://openrouter.ai
# Your API key should already be associated with the Arena credit grant

# Set your API key as environment variable
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Test that it works (simple curl)
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-sonnet-4-5-20250929",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Check your credit balance
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

**Model selection strategy:**
- Days 1-5 (iteration): Use a cheap, fast model. Good candidates:
  - `anthropic/claude-haiku-4-5-20251001` — fast, cheap, decent reasoning
  - `openai/gpt-4.1-mini` — very cheap, good code generation
- Days 6-11 (optimization): Step up to mid-tier:
  - `anthropic/claude-sonnet-4-5-20250929` — strong balance of capability and cost
  - `openai/gpt-4.1` — good document comprehension
- Days 12-14 (final runs): Use frontier:
  - `anthropic/claude-opus-4-6` — best document reasoning in published results
  - `openai/gpt-5.3` or `openai/gpt-5.4` — strong agents

**Check current model pricing at:** https://openrouter.ai/models — prices change, verify before committing to a model for a long run.

## 3. Daytona ($100 credit)

Daytona provides code execution sandboxes. This is where the agent actually runs code.

```bash
# Install Daytona CLI
# Check https://www.daytona.io/docs for latest install instructions
curl -sf -L https://download.daytona.io/daytona/install.sh | sudo bash

# Or via Homebrew (macOS)
brew install daytonaio/tap/daytona

# Authenticate
daytona login

# Create a workspace (sandbox for agent execution)
daytona create --provider=docker

# List workspaces
daytona list

# Open a workspace
daytona open <workspace-name>
```

**How Daytona fits:** The coding agent (OpenHands) executes shell commands and Python code inside Daytona sandboxes. This is the "compute" environment where the agent reads documents, writes scripts, and runs them. The Arena infrastructure likely handles Daytona integration automatically through the arena.yaml config, but verify during reconnaissance.

## 4. Dedalus ($100 credit)

Dedalus provides MCP server hosting and agent orchestration. This is how you give the agent additional tools.

```bash
# Check https://dedalus.dev or https://docs.dedalus.dev for latest instructions
# Dedalus may be accessed via web console or CLI

# The key use case: host an MCP server for document search
# This would let the agent query "find Treasury Bulletins about defense spending 1940"
# instead of manually browsing the filesystem
```

**Potential MCP server setup:** If you can host a vector search MCP server over the parsed Treasury Bulletin corpus, it dramatically improves retrieval. The server would:
1. Index all transformed TXT files with embeddings
2. Accept natural language queries from the agent
3. Return the most relevant document filenames and page ranges
4. Expose this as an MCP tool the agent can call

**Whether this is worth it depends on what Arena provides out of the box.** If the Arena environment already has good retrieval tools, MCP may be unnecessary. If the agent has to browse raw files, MCP retrieval becomes very high value. Decide after reconnaissance.

## 5. OpenHands (The Coding Agent)

OpenHands is the pre-built coding agent you're configuring. Arena likely provides its own OpenHands integration, but for local testing:

```bash
# Install OpenHands CLI (requires Python 3.12+ and uv)
pip install uv  # if not already installed
uvx openhands

# Or via the SDK for custom agent work
git clone https://github.com/OpenHands/agent-sdk.git
cd agent-sdk
make build
```

**OpenHands capabilities relevant to Arena:**
- Bash command execution (for file operations, grep, search)
- Python/Jupyter code execution (for computation)
- File reading and editing
- MCP server integration
- Task tracking

## 6. OfficeQA Benchmark Data

```bash
# Clone the OfficeQA repo (contains questions, answers, and parsed documents)
git clone https://github.com/databricks/officeqa.git
cd officeqa

# The key files:
# officeqa_full.csv — all 246 questions with answers and source file references
# reward.py — the scoring function (1% fuzzy numeric tolerance)
# treasury_bulletins_parsed/transformed/ — the pre-parsed TXT files (~200MB)
# treasury_bulletins_parsed/jsons/ — the full parsed JSON (~600MB)

# Download the transformed text files (highest priority)
cd treasury_bulletins_parsed
# Unzip the archives — they contain the TXT files that produced the best performance
unzip transformed/*.zip -d transformed/

# Study the question distribution
python3 -c "
import pandas as pd
df = pd.read_csv('officeqa_full.csv')
print(f'Total questions: {len(df)}')
print(f'Easy: {len(df[df.difficulty==\"easy\"])}')
print(f'Hard: {len(df[df.difficulty==\"hard\"])}')
print(f'Sample question: {df.iloc[0].question[:200]}')
print(f'Sample answer: {df.iloc[0].answer}')
print(f'Sample source: {df.iloc[0].source_files}')
"
```

## 7. Environment Variables

Add these to your shell profile (~/.zshrc or ~/.bashrc):

```bash
# Arena and tool credentials
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export ARENA_TOKEN="your-arena-auth-token"

# Optional: Daytona and Dedalus if they use env vars
export DAYTONA_API_KEY="your-daytona-key"
export DEDALUS_API_KEY="your-dedalus-key"

# Project paths
export ARENA_PROJECT="$HOME/arena-cohort0"
export OFFICEQA_REPO="$HOME/officeqa"
```

## 8. Day 1 Checklist

Run these in order on your first day:

```bash
# 1. Install Arena CLI and authenticate
# 2. Run arena init — INSPECT EVERYTHING before changing anything
# 3. Clone OfficeQA repo, download parsed documents
# 4. Set up OpenRouter API key, test connectivity
# 5. Study arena.yaml structure → document in notes/recon_findings.md
# 6. Study 5-10 sample questions from officeqa_full.csv manually
# 7. Run baseline submission with default config → record score
# 8. Update SCRATCHPAD.md with all findings
```
