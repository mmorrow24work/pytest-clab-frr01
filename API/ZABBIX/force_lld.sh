#!/usr/bin/env bash
# Force Zabbix LLD (network interface discovery) to run immediately
# by temporarily setting the interval to 30s, waiting, then restoring to 1h.
# Run after a fresh Zabbix start to avoid waiting the default 1h delay.
#
# Usage: ./force_lld.sh [hostid1 hostid2 ...]
# If no hostids given, targets the 6 frr01 clab hosts.

TOKEN=$(cat "$(dirname "$0")/../../zabbix_token.txt")
HOSTIDS="${@:-10786 10787 10788 10789 10790 10791}"

zabbix_api() {
  curl -s http://localhost/api_jsonrpc.php \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d "$1"
}

echo "=== Collecting LLD rule IDs ==="
declare -a ITEM_IDS=()
for hid in $HOSTIDS; do
  result=$(zabbix_api "{\"jsonrpc\":\"2.0\",\"method\":\"discoveryrule.get\",\"params\":{\"output\":[\"itemid\",\"name\",\"key_\"],\"hostids\":\"$hid\",\"search\":{\"key_\":\"net.if.discovery\"}},\"id\":1}")
  itemid=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('result',[]); print(r[0]['itemid'] if r else '')" 2>/dev/null)
  if [ -n "$itemid" ]; then
    ITEM_IDS+=("$itemid")
    echo "  hostid=$hid → itemid=$itemid"
  fi
done

echo ""
echo "=== Setting LLD delay to 30s ==="
for itemid in "${ITEM_IDS[@]}"; do
  zabbix_api "{\"jsonrpc\":\"2.0\",\"method\":\"discoveryrule.update\",\"params\":{\"itemid\":\"$itemid\",\"delay\":\"30s\"},\"id\":1}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('  itemid=$itemid updated:', bool(d.get('result')))" 2>/dev/null
done

echo ""
echo "=== Waiting 75s for LLD to run ==="
sleep 75

echo ""
echo "=== Restoring LLD delay to 1h ==="
for itemid in "${ITEM_IDS[@]}"; do
  zabbix_api "{\"jsonrpc\":\"2.0\",\"method\":\"discoveryrule.update\",\"params\":{\"itemid\":\"$itemid\",\"delay\":\"1h\"},\"id\":1}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('  itemid=$itemid restored:', bool(d.get('result')))" 2>/dev/null
done

echo ""
echo "=== Done — LLD discovery complete ==="
