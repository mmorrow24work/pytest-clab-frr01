#!/usr/bin/env bash
# Run the original test suite + EXTRAS suite in a continuous loop for 30 minutes.
# Pushes per-run metrics to Zabbix after each iteration.
# Press Ctrl-C to stop early. Zabbix and clab are NOT stopped on exit.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAB_DIR="/home/mickm/git/containerlab/lab-examples/frr01"
PYTEST="/home/mickm/git/pytest-virtual-environment/.venv/bin/pytest"
REPORTS_DIR="$PROJECT_DIR/reports"
LOG_FILE="$REPORTS_DIR/extras-summary.log"

ZABBIX_HOST="containerlab-frr01"
ZABBIX_SERVER="localhost"
ZABBIX_PORT=10051

DURATION_MINS=30
END_TIME=$(( $(date +%s) + DURATION_MINS * 60 ))

ORIGINAL_TESTS=(
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

EXTRAS_TESTS=(
  "$PROJECT_DIR/EXTRAS/tests/test_13_iperf_pc1_to_pc2.py"
  "$PROJECT_DIR/EXTRAS/tests/test_14_iperf_pc2_to_pc3.py"
  "$PROJECT_DIR/EXTRAS/tests/test_15_iperf_router_backbone.py"
  "$PROJECT_DIR/EXTRAS/tests/test_16_iperf_vlan100.py"
  "$PROJECT_DIR/EXTRAS/tests/test_17_iperf_parallel.py"
  "$PROJECT_DIR/EXTRAS/tests/test_18_snmp_trap_coldstart.py"
  "$PROJECT_DIR/EXTRAS/tests/test_19_snmp_trap_all_routers.py"
  "$PROJECT_DIR/EXTRAS/tests/test_20_snmp_trap_linkdown_oid.py"
  "$PROJECT_DIR/EXTRAS/tests/test_21_snmp_trap_custom_string.py"
  "$PROJECT_DIR/EXTRAS/tests/test_22_snmp_trap_zabbix.py"
)

mkdir -p "$REPORTS_DIR"
RUN_COUNT=0

run_once() {
  RUN_START=$(date +%s)
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)

  echo ""
  echo "****************************"
  echo "$(date)  [run $((RUN_COUNT + 1))]"
  echo "****************************"
  echo ""

  cd "$CLAB_DIR"
  set +e
  "$PYTEST" -v -s --tb=short \
    --html="$REPORTS_DIR/report_extras.html" --self-contained-html \
    "${ORIGINAL_TESTS[@]}" "${EXTRAS_TESTS[@]}" > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  set -e

  DURATION=$(( $(date +%s) - RUN_START ))

  PASSED=$(grep -oP '\d+(?= passed)' "$LOG_FILE" || echo 0)
  FAILED=$(grep -oP '\d+(?= failed)' "$LOG_FILE" || echo 0)
  TOTAL=$(( ${PASSED:-0} + ${FAILED:-0} ))

  echo "Run $TIMESTAMP: passed=${PASSED:-0} failed=${FAILED:-0} exit=${EXIT_CODE} duration=${DURATION}s"

  TMPFILE=$(mktemp)
  cat > "$TMPFILE" <<EOF
$ZABBIX_HOST pytest.exit_code $EXIT_CODE
$ZABBIX_HOST pytest.tests_total $TOTAL
$ZABBIX_HOST pytest.tests_passed ${PASSED:-0}
$ZABBIX_HOST pytest.tests_failed ${FAILED:-0}
$ZABBIX_HOST pytest.run_duration_seconds $DURATION
EOF
  zabbix_sender -z "$ZABBIX_SERVER" -p "$ZABBIX_PORT" -i "$TMPFILE" || true
  rm -f "$TMPFILE"

  RUN_COUNT=$(( RUN_COUNT + 1 ))
}

echo "Starting combined loop: original (10) + EXTRAS (10) tests"
echo "Duration: ${DURATION_MINS} minutes  (until $(date -d "@$END_TIME" '+%H:%M:%S' 2>/dev/null || date -r "$END_TIME" '+%H:%M:%S' 2>/dev/null || echo "$(date)"))"
echo ""

while [ "$(date +%s)" -lt "$END_TIME" ]; do
  run_once
  REMAINING=$(( END_TIME - $(date +%s) ))
  if [ "$REMAINING" -gt 5 ]; then
    echo "Sleeping 5s... ($REMAINING s remaining)"
    sleep 5
  fi
done

echo ""
echo "=============================="
echo "Loop complete: $RUN_COUNT runs"
echo "=============================="
echo "Zabbix and clab network left running."
