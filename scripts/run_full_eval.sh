#!/bin/bash
# Full 246-question evaluation with resume support
# Adapted from arena-toolkit by Ground Wire team
#
# Usage:
#   source .env && bash scripts/run_full_eval.sh
#
# Optional:
#   BATCH_SIZE=10 source .env && bash scripts/run_full_eval.sh

set -e
cd "$(dirname "$0")/.."

SAMPLES_DIR=".arena/samples"
BACKUP_DIR="/tmp/arena-samples-backup-dolores"
RESULTS_DIR="results/full_eval"
LOG_DIR="results/logs"
BATCH_SIZE="${BATCH_SIZE:-10}"

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

echo "╔═══════════════════════════════════════════════════╗"
echo "║  FULL 246-QUESTION OFFICEQA EVALUATION            ║"
echo "║  Dolores Research — $(date '+%Y-%m-%d %H:%M')              ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "  Batch size: $BATCH_SIZE"
echo "  Model: $(grep 'model:' arena.yaml | head -1 | awk '{print $2}' | tr -d '\"')"
echo "  Harness: $(grep 'harness_name:' arena.yaml | head -1 | awk '{print $2}' | tr -d '\"')"
echo ""

# Verify API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY not set. Run: source .env"
    exit 1
fi
echo "  API key: ${OPENROUTER_API_KEY:0:12}..."

# Backup samples if not already backed up
if [ ! -d "$BACKUP_DIR" ]; then
    cp -r "$SAMPLES_DIR" "$BACKUP_DIR"
    echo "  Samples backed up to $BACKUP_DIR"
else
    echo "  Using existing backup at $BACKUP_DIR"
fi

# Collect ALL sample UIDs from backup
ALL_UIDS=$(ls "$BACKUP_DIR" | grep "^officeqa-" | sort)
TOTAL=$(echo "$ALL_UIDS" | wc -l | tr -d ' ')
echo "  Total samples: $TOTAL"

# Split into batches
SPLIT_DIR="/tmp/arena-batch-splits-dolores"
rm -rf "$SPLIT_DIR"
mkdir -p "$SPLIT_DIR"
echo "$ALL_UIDS" | split -l "$BATCH_SIZE" - "$SPLIT_DIR/chunk_"

NUM_BATCHES=$(ls "$SPLIT_DIR"/chunk_* | wc -l | tr -d ' ')
echo "  Batches: $NUM_BATCHES (of $BATCH_SIZE each)"
echo ""

BATCH_NUM=0
TOTAL_PASS=0
TOTAL_FAIL=0

for batch_file in "$SPLIT_DIR"/chunk_*; do
    BATCH_NUM=$((BATCH_NUM + 1))
    BATCH_UIDS=$(cat "$batch_file")
    BATCH_COUNT=$(echo "$BATCH_UIDS" | wc -l | tr -d ' ')
    TAG="full246-b${BATCH_NUM}"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  BATCH $BATCH_NUM / $NUM_BATCHES ($BATCH_COUNT tasks)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Resume: check if this batch already has results
    BATCH_RESULT_FILE="$RESULTS_DIR/${TAG}.json"
    if [ -f "$BATCH_RESULT_FILE" ]; then
        B_PASS=$(python3 -c "import json; d=json.load(open('$BATCH_RESULT_FILE')); print(d.get('passed',0))" 2>/dev/null || echo 0)
        B_FAIL=$(python3 -c "import json; d=json.load(open('$BATCH_RESULT_FILE')); print(d.get('failed',0))" 2>/dev/null || echo 0)
        echo "  SKIPPING (already completed: $B_PASS pass, $B_FAIL fail)"
        TOTAL_PASS=$((TOTAL_PASS + B_PASS))
        TOTAL_FAIL=$((TOTAL_FAIL + B_FAIL))
        echo ""
        continue
    fi

    # Clear samples dir and populate with this batch only
    rm -rf "$SAMPLES_DIR"/*
    cp "$BACKUP_DIR/manifest.json" "$SAMPLES_DIR/" 2>/dev/null || echo '{"version":"batch"}' > "$SAMPLES_DIR/manifest.json"

    for uid in $BATCH_UIDS; do
        if [ -d "$BACKUP_DIR/$uid" ]; then
            cp -r "$BACKUP_DIR/$uid" "$SAMPLES_DIR/$uid"
        fi
    done

    LOADED=$(ls "$SAMPLES_DIR" | grep -c officeqa || echo 0)
    echo "  Loaded $LOADED tasks into samples dir"

    # Clean Docker between batches
    docker network prune -f > /dev/null 2>&1
    docker container prune -f > /dev/null 2>&1

    # Run arena test
    echo "  Running: arena test --all --tag $TAG"
    arena test --all --tag "$TAG" 2>&1 | tee "$LOG_DIR/${TAG}.log"

    # Parse results from the run directory
    RUN_DIR=$(ls -dt .arena/runs/run-* 2>/dev/null | head -1)
    if [ -n "$RUN_DIR" ]; then
        RESULTS=$(python3 -c "
import json, glob, os
run_dir = '$RUN_DIR'
# Find the tag directory inside the run
tag_dirs = [d for d in os.listdir(run_dir) if os.path.isdir(os.path.join(run_dir, d))]
results_file = os.path.join(run_dir, 'results.json')
if os.path.exists(results_file):
    d = json.load(open(results_file))
    passed = d.get('tasks_passed', 0)
    failed = d.get('tasks_failed', 0)
    cost = d.get('total_cost_usd', 0)
    latency = d.get('avg_latency_sec', 0)
    # Get per-task results
    tasks = d.get('tasks', [])
    task_results = {}
    for t in tasks:
        status = 'pass' if t.get('status') == 'passed' else 'fail'
        task_results[t['task_id']] = {
            'status': status,
            'cost': t.get('cost_usd', 0),
            'latency': t.get('latency_sec', 0),
        }
    print(f'PASSED={passed} FAILED={failed} COST={cost:.2f} LATENCY={latency:.0f}')
else:
    print('PASSED=0 FAILED=0 COST=0 LATENCY=0')
" 2>/dev/null) || RESULTS="PASSED=0 FAILED=0 COST=0 LATENCY=0"
        eval "$RESULTS"
    else
        PASSED=0; FAILED=0; COST=0; LATENCY=0
    fi

    TOTAL_PASS=$((TOTAL_PASS + PASSED))
    TOTAL_FAIL=$((TOTAL_FAIL + FAILED))

    # Save per-batch result with task-level detail
    python3 << PYEOF
import json, os, glob

batch_result = {
    'tag': '$TAG',
    'batch': $BATCH_NUM,
    'passed': $PASSED,
    'failed': $FAILED,
    'cost': $COST,
    'avg_latency': $LATENCY,
    'uids': $(echo "$BATCH_UIDS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip().split('\n')))"),
    'tasks': {}
}

# Try to get per-task results from the run
run_dir = '$RUN_DIR'
results_file = os.path.join(run_dir, 'results.json') if run_dir else ''
if os.path.exists(results_file):
    d = json.load(open(results_file))
    for t in d.get('tasks', []):
        batch_result['tasks'][t['task_id']] = {
            'status': 'pass' if t.get('status') == 'passed' else 'fail',
            'cost': t.get('cost_usd', 0),
            'latency': t.get('latency_sec', 0),
        }

with open('$BATCH_RESULT_FILE', 'w') as f:
    json.dump(batch_result, f, indent=2)
PYEOF

    echo "  Batch $BATCH_NUM: $PASSED pass, $FAILED fail, cost=\$$COST"
    echo "  Running total: $TOTAL_PASS pass, $TOTAL_FAIL fail"
    echo ""
done

# Restore original samples
rm -rf "$SAMPLES_DIR"
cp -r "$BACKUP_DIR" "$SAMPLES_DIR"
echo "  Original samples restored"

# Run aggregation
echo ""
python3 scripts/aggregate_results.py

echo ""
echo "═══════════════════════════════════════════"
echo "  EVALUATION COMPLETE"
echo "  Results saved to: $RESULTS_DIR/"
echo "  Logs saved to: $LOG_DIR/"
echo "═══════════════════════════════════════════"
