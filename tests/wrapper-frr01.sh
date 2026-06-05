#!/usr/bin/env bash
set -euo pipefail
set -x

HOSTNAME="containerlab-frr01"        # Zabbix host name used to access pytest metrics and reports
SERVER="localhost"                   # Zabbix server IP/FQDN
PORT=10051                           # default Zabbix port

PROJECT_DIR="/home/mickm/git/containerlab/lab-examples/frr01"
TEST_DIR="$PROJECT_DIR/tests"
REPORTS_DIR="$PROJECT_DIR/tests/reports"
LOG_FILE="$TEST_DIR/pytest-summary.log"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="$REPORTS_DIR/report.html"

# Run pytest from project root so helpers.py and zabbix_token.txt are found
cd "$PROJECT_DIR"
set +e
pytest -q --tb=no --html="$REPORT_FILE" --self-contained-html tests/ > "$LOG_FILE" 2>&1
EXIT_CODE=$?
set -e

# Parse the summary line e.g. "9 failed, 11 passed in 26.09s"
PASSED=$(grep -oP '\d+(?= passed)' "$LOG_FILE" || echo 0)
FAILED=$(grep -oP '\d+(?= failed)' "$LOG_FILE" || echo 0)
TOTAL=$(( ${PASSED:-0} + ${FAILED:-0} ))

# Write all metrics to a temp file for zabbix_sender -i (input mode)
TMPFILE=$(mktemp)
cat > "$TMPFILE" <<EOF
$HOSTNAME pytest.exit_code $EXIT_CODE
$HOSTNAME pytest.tests_total $TOTAL
$HOSTNAME pytest.tests_passed $PASSED
$HOSTNAME pytest.tests_failed ${FAILED:-0}
EOF

# Send all metrics in one call
zabbix_sender -z "$SERVER" -p "$PORT" -i "$TMPFILE" || true

rm -f "$TMPFILE"

# Commit report to git history (FIXED: add/commit first, then pull, then push)
# git -C "$REPORTS_DIR" checkout main 2>/dev/null || git -C "$REPORTS_DIR" checkout -b main
# git -C "$REPORTS_DIR" add report.html
# git -C "$REPORTS_DIR" commit -m "run $TIMESTAMP | passed=$PASSED failed=$FAILED exit=$EXIT_CODE"
# git -C "$REPORTS_DIR" pull --no-edit origin main 2>/dev/null || true
# git -C "$REPORTS_DIR" push origin main

# Simplify the git block
git -C "$REPORTS_DIR" add report.html
git -C "$REPORTS_DIR" commit -m "run $TIMESTAMP | passed=$PASSED failed=$FAILED exit=$EXIT_CODE" || true
git -C "$REPORTS_DIR" push origin main


