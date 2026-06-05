#!/usr/bin/env bash
# Run the full pytest suite continuously and push results to Zabbix after each run.
# Press Ctrl-C to stop. Results are written to reports/report.html.
# Zabbix metrics (exit_code, total, passed, failed) are sent via zabbix_sender.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAB_DIR="/home/mickm/git/containerlab/lab-examples/frr01"
PYTEST="/home/mickm/git/pytest-virtual-environment/.venv/bin/pytest"
REPORTS_DIR="$PROJECT_DIR/reports"
LOG_FILE="$REPORTS_DIR/pytest-summary.log"
INTERVAL=5

ZABBIX_HOST="containerlab-frr01"
ZABBIX_SERVER="localhost"
ZABBIX_PORT=10051

TESTS=(
  tests/test_01_log_output-mgmt_cli.py
  tests/test_02_log_output_interfaces_cli.py
  tests/test_04_get_hosts_zabbix.py
  tests/test_05_log_output_backup_configs.py
  tests/test_06_log_output_shutdown_router1_eth1_100.py
  tests/test_07_mgmt_cli_after_failure.py
  tests/test_08_log_output_get_vlans_zabbix.py
  tests/test_09_log_output_zabbix_problem_after_interface_shutdown.py
  tests/test_11_no_output_restore_router1_eth1_100.py
  tests/test_12_interfaces_zabbix_after_failure.py
)

mkdir -p "$REPORTS_DIR"

run_once() {
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  REPORT_FILE="$REPORTS_DIR/report.html"

  echo ""
  echo "****************************"
  echo "$(date)"
  echo "****************************"
  echo ""

  # Run pytest from the clab directory (helpers.py needs frr01.clab.yml on disk)
  cd "$CLAB_DIR"
  set +e
  "$PYTEST" -v -s --tb=short \
    --html="$REPORT_FILE" --self-contained-html \
    "${TESTS[@]}" > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  set -e

  # Parse summary line
  PASSED=$(grep -oP '\d+(?= passed)' "$LOG_FILE" || echo 0)
  FAILED=$(grep -oP '\d+(?= failed)' "$LOG_FILE" || echo 0)
  TOTAL=$(( ${PASSED:-0} + ${FAILED:-0} ))

  echo "Run $TIMESTAMP: passed=${PASSED:-0} failed=${FAILED:-0} exit=${EXIT_CODE}"

  # Push to Zabbix
  TMPFILE=$(mktemp)
  cat > "$TMPFILE" <<EOF
$ZABBIX_HOST pytest.exit_code $EXIT_CODE
$ZABBIX_HOST pytest.tests_total $TOTAL
$ZABBIX_HOST pytest.tests_passed ${PASSED:-0}
$ZABBIX_HOST pytest.tests_failed ${FAILED:-0}
EOF
  zabbix_sender -z "$ZABBIX_SERVER" -p "$ZABBIX_PORT" -i "$TMPFILE" || true
  rm -f "$TMPFILE"
}

echo "Starting continuous test loop. Ctrl-C to stop."
echo "Interval between runs: ${INTERVAL}s"
echo ""

while true; do
  run_once
  echo "Sleeping ${INTERVAL}s..."
  sleep "$INTERVAL"
done
