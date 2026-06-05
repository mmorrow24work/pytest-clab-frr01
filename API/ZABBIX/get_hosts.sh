#!/usr/bin/env bash
# List all Zabbix hosts via the JSON-RPC API.
# Requires zabbix_token.txt in the project root.

TOKEN=$(cat "$(dirname "$0")/../../zabbix_token.txt")

curl -s http://localhost/api_jsonrpc.php \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
      "output": ["hostid", "host", "name", "status"]
    },
    "id": 1
  }' | python3 -m json.tool
