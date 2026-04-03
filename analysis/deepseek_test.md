# DeepSeek V3.2 Test Report
**Date:** March 26, 2026
**Purpose:** Evaluate DeepSeek V3.2 as alternative to Claude Sonnet 4.6 for Arena submission
**Model:** deepseek/deepseek-v3.2 via OpenRouter
**Pricing:** $0.26/M input, $0.38/M output tokens (vs Sonnet 4.6 at $3.00/$15.00)
**Cost ratio:** ~10-15x cheaper than Sonnet 4.6

## Background

DeepSeek V3.2 was previously tested on March 23, 2026 with the `openhands` harness and failed completely (0.0 score) due to tool calling format incompatibility with OpenHands. This test uses `openhands-sdk` which may handle tool calling differently.

The strategic value of a strong DeepSeek result is high: it would demonstrate that behavioral engineering (skills/prompts) matters more than raw model capability, directly validating the Dolores Research thesis.

## Configuration

Using identical configuration to our Sonnet 4.6 setup except for the model string:
- Harness: openhands-sdk
- Skills: 5 files (methodology, retrieval_strategy, known_pitfalls, computation_patterns, table_parsing_guide)
- All gap fixes from iterations 2-3 included (output formatting, web search, unit conversion, etc.)
- Only change: model field in arena.yaml

## Phase 1: Single Question Compatibility Test
[TO BE FILLED]

## Phase 2: Full 20-Question Sample Run
[TO BE FILLED]

## Phase 3: Failure Analysis and Comparison
[TO BE FILLED]

## Conclusions and Recommendations
[TO BE FILLED]
