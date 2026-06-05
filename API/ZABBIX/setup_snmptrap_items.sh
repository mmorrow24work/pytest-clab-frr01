#!/usr/bin/env bash
# Adds an SNMP interface and snmptrap.fallback item to each router host in Zabbix.
# This is the same setup performed automatically by EXTRAS/conftest.py, but
# can also be run manually to prepare Zabbix before running EXTRAS tests.
#
# Requires: zabbix_token.txt in the current directory or ../
# Usage: bash API/ZABBIX/setup_snmptrap_items.sh

TOKEN_FILE=""
for f in zabbix_token.txt ../zabbix_token.txt; do
  [ -f "$f" ] && TOKEN_FILE="$f" && break
done
[ -z "$TOKEN_FILE" ] && { echo "ERROR: zabbix_token.txt not found"; exit 1; }
TOKEN=$(cat "$TOKEN_FILE")

ZBX="http://localhost/api_jsonrpc.php"
COMMUNITY="public"

declare -A ROUTER_IPS=(
  ["router1"]="172.18.0.41"
  ["router2"]="172.18.0.42"
  ["router3"]="172.18.0.43"
)

zbx_call() {
  local method="$1"
  local params="$2"
  curl -s -X POST "$ZBX" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"$method\",\"params\":$params,\"id\":1}" \
    | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'error' in d:
    print('ERROR:', d['error']['data'], file=sys.stderr)
    sys.exit(1)
print(json.dumps(d.get('result',{})))
"
}

for HOST_NAME in router1 router2 router3; do
  IP="${ROUTER_IPS[$HOST_NAME]}"
  echo "=== $HOST_NAME ($IP) ==="

  # Get hostid and existing interfaces
  HOST_DATA=$(zbx_call "host.get" "{\"output\":[\"hostid\",\"name\"],\"selectInterfaces\":[\"interfaceid\",\"type\",\"ip\"],\"filter\":{\"name\":[\"$HOST_NAME\"]}}")
  HOSTID=$(echo "$HOST_DATA" | python3 -c "import sys,json; h=json.load(sys.stdin); print(h[0]['hostid'] if h else '')")
  [ -z "$HOSTID" ] && echo "  Host not found, skipping" && continue
  echo "  hostid: $HOSTID"

  # Check for existing SNMP interface
  SNMP_IFACE_ID=$(echo "$HOST_DATA" | python3 -c "
import sys,json
h=json.load(sys.stdin)
ifaces=[i for i in h[0]['interfaces'] if i['type']=='2']
print(ifaces[0]['interfaceid'] if ifaces else '')
")

  if [ -z "$SNMP_IFACE_ID" ]; then
    echo "  Adding SNMP interface..."
    SNMP_IFACE_ID=$(zbx_call "hostinterface.create" "{
      \"hostid\":\"$HOSTID\",\"main\":\"1\",\"type\":\"2\",\"useip\":\"1\",
      \"ip\":\"$IP\",\"dns\":\"\",\"port\":\"161\",
      \"details\":{\"version\":\"2\",\"community\":\"$COMMUNITY\",\"bulk\":\"1\",
                   \"securityname\":\"\",\"securitylevel\":\"0\",
                   \"authpassphrase\":\"\",\"privpassphrase\":\"\",
                   \"authprotocol\":\"0\",\"privprotocol\":\"0\",\"contextname\":\"\"}
    }" | python3 -c "import sys,json; print(json.load(sys.stdin)['interfaceids'][0])")
    echo "  Created SNMP interface id: $SNMP_IFACE_ID"
  else
    echo "  SNMP interface already exists: $SNMP_IFACE_ID"
  fi

  # Check for existing snmptrap.fallback item
  ITEM_ID=$(zbx_call "item.get" "{\"output\":[\"itemid\"],\"hostids\":[\"$HOSTID\"],\"search\":{\"key_\":\"snmptrap.fallback\"}}" \
    | python3 -c "import sys,json; items=json.load(sys.stdin); print(items[0]['itemid'] if items else '')")

  if [ -z "$ITEM_ID" ]; then
    echo "  Creating snmptrap.fallback item..."
    ITEM_ID=$(zbx_call "item.create" "{
      \"hostid\":\"$HOSTID\",
      \"name\":\"SNMP traps (fallback)\",
      \"key_\":\"snmptrap.fallback\",
      \"type\":\"17\",
      \"value_type\":\"2\",
      \"delay\":\"0\",
      \"logtimefmt\":\"hh:mm:ssdd/MM/yyyy\",
      \"interfaceid\":\"$SNMP_IFACE_ID\"
    }" | python3 -c "import sys,json; print(json.load(sys.stdin)['itemids'][0])")
    echo "  Created item id: $ITEM_ID"
  else
    echo "  snmptrap.fallback item already exists: $ITEM_ID"
  fi
done

echo ""
echo "Done. Run EXTRAS tests to verify trap delivery:"
echo "  cd ~/git/containerlab/lab-examples/frr01"
echo "  pytest -v -s ~/git/pytest-clab-frr01/EXTRAS/tests/test_1[89]*.py test_2[012]*.py"
