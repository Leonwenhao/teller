#!/bin/bash
# Simple rerun — runs each question individually with arena test --filter
# No sample swapping. No stdin issues. Just works.
#
# Usage: source .env && bash scripts/run_rerun.sh

cd "$(dirname "$0")/.."

RESULTS_DIR="results/full_eval"
LOG_DIR="results/logs"
RERUN_LIST="results/rerun_list.json"

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

# Get all UIDs to rerun
python3 -c "
import json
uids = json.load(open('$RERUN_LIST'))
for uid in sorted(uids):
    print(uid.lower())
" > /tmp/rerun_uids.txt

TOTAL=$(wc -l < /tmp/rerun_uids.txt | tr -d ' ')
echo "╔═══════════════════════════════════════════════════╗"
echo "║  RERUN: $TOTAL questions, one at a time             ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

COUNT=0
PASS=0
FAIL=0
INFRA=0

while IFS= read -r uid; do
    COUNT=$((COUNT + 1))
    SAMPLE="officeqa-${uid}"
    DONE_FILE="$RESULTS_DIR/done-${uid}.json"

    # Skip if already completed
    if [ -f "$DONE_FILE" ]; then
        PREV=$(python3 -c "import json; print(json.load(open('$DONE_FILE')).get('status','?'))" 2>/dev/null)
        echo "[$COUNT/$TOTAL] $uid — SKIP ($PREV)"
        case "$PREV" in
            pass) PASS=$((PASS + 1)) ;;
            fail) FAIL=$((FAIL + 1)) ;;
            *) INFRA=$((INFRA + 1)) ;;
        esac
        continue
    fi

    echo -n "[$COUNT/$TOTAL] $uid — "

    # Run single question
    arena test --filter "$SAMPLE" --tag "rerun-${uid}" < /dev/null > "$LOG_DIR/rerun-${uid}.log" 2>&1
    EXIT_CODE=$?

    # Parse result from the run directory
    RESULT=$(python3 -c "
import json, glob, os
for rd in sorted(glob.glob('.arena/runs/run-*'), reverse=True):
    rf = os.path.join(rd, 'rerun-${uid}', 'result.json')
    if not os.path.exists(rf):
        continue
    d = json.load(open(rf))
    stats = list(d.get('stats',{}).get('evals',{}).values())
    if not stats:
        continue
    s = stats[0]
    rewards = s.get('reward_stats',{}).get('reward',{})
    for score_str, tasks in rewards.items():
        if tasks:
            status = 'pass' if float(score_str) >= 1.0 else 'fail'
            print(status)
            exit()
    exc = s.get('exception_stats',{})
    if exc:
        print('infra')
        exit()
    break
print('unknown')
" 2>/dev/null)

    # Save individual result
    python3 -c "
import json
json.dump({'uid': '${uid}', 'status': '${RESULT}'}, open('$DONE_FILE', 'w'))
"

    case "$RESULT" in
        pass)
            echo "PASS ✓"
            PASS=$((PASS + 1))
            ;;
        fail)
            echo "FAIL ✗"
            FAIL=$((FAIL + 1))
            ;;
        *)
            echo "INFRA ⚠ ($RESULT)"
            INFRA=$((INFRA + 1))
            ;;
    esac

    # Docker cleanup every 10 questions
    if [ $((COUNT % 10)) -eq 0 ]; then
        docker network prune -f > /dev/null 2>&1
        docker container prune -f > /dev/null 2>&1
    fi

done < /tmp/rerun_uids.txt

echo ""
echo "═══════════════════════════════════════════"
echo "  COMPLETE: ${PASS}P ${FAIL}F ${INFRA}I out of $TOTAL"
echo "═══════════════════════════════════════════"
