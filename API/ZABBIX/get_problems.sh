#!/usr/bin/env bash
# Get recent Zabbix problems (active and resolved) via the JSON-RPC API.
# Requires zabbix_token.txt in the project root.

TOKEN=$(cat "$(dirname "$0")/../../zabbix_token.txt")

curl -s http://localhost/api_jsonrpc.php \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "problem.get",
    "params": {
      "output": ["eventid", "name", "severity", "clock"],
      "sortfield": ["eventid"],
      "sortorder": "DESC",
      "recent": true,
      "limit": 20
    },
    "id": 1
  }' | python3 -m json.tool
