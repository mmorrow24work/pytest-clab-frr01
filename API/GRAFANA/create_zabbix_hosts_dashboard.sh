#!/usr/bin/env bash
# Creates the clab frr01 Zabbix Host Status dashboard in Grafana via REST API.
# Run from the project root. Grafana must be running on http://localhost:5000.

GRAFANA_URL="http://localhost:5000"
ZABBIX_DS_UID="efnqaelol143kc"

curl -s -u admin:admin -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -d '{
  "dashboard": {
    "uid": "clab-frr01-hosts",
    "title": "clab frr01 — Zabbix Host Status",
    "tags": ["zabbix", "containerlab", "frr01"],
    "timezone": "browser",
    "schemaVersion": 39,
    "refresh": "30s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
      {
        "id": 1,
        "title": "Routers — eth0 Bits Received",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "fieldConfig": {
          "defaults": {"unit": "bps", "color": {"mode": "palette-classic"}, "custom": {"lineWidth": 2, "fillOpacity": 10}}
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [
          {"refId":"A","group":{"filter":""},"host":{"filter":"router1"},"application":{"filter":"Network interfaces"},"item":{"filter":"/eth0.*Bits received/"},"functions":[]},
          {"refId":"B","group":{"filter":""},"host":{"filter":"router2"},"application":{"filter":"Network interfaces"},"item":{"filter":"/eth0.*Bits received/"},"functions":[]},
          {"refId":"C","group":{"filter":""},"host":{"filter":"router3"},"application":{"filter":"Network interfaces"},"item":{"filter":"/eth0.*Bits received/"},"functions":[]}
        ]
      },
      {
        "id": 2,
        "title": "Routers — eth0 Bits Sent",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "fieldConfig": {
          "defaults": {"unit": "bps", "color": {"mode": "palette-classic"}, "custom": {"lineWidth": 2, "fillOpacity": 10}}
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [
          {"refId":"A","group":{"filter":""},"host":{"filter":"/router.*/"},"application":{"filter":"Network interfaces"},"item":{"filter":"/eth0.*Bits sent/"},"functions":[]}
        ]
      },
      {
        "id": 3,
        "title": "router1 — VLAN 100 Interface Traffic",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "fieldConfig": {
          "defaults": {"unit": "bps", "color": {"fixedColor": "orange", "mode": "fixed"}, "custom": {"lineWidth": 2, "fillOpacity": 10}}
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [
          {"refId":"A","group":{"filter":""},"host":{"filter":"router1"},"application":{"filter":"Network interfaces"},"item":{"filter":"/eth1.100.*Bits/"},"functions":[]}
        ]
      },
      {
        "id": 4,
        "title": "pytest Last Run Result",
        "type": "stat",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "background", "textMode": "auto"},
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {"mode": "absolute", "steps": [{"color": "red","value": null},{"color": "green","value": 1}]},
            "unit": "short",
            "noValue": "0"
          }
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [
          {"refId":"A","group":{"filter":""},"host":{"filter":"containerlab-frr01"},"application":{"filter":""},"item":{"filter":"pytest.tests_passed"},"functions":[]}
        ]
      }
    ]
  },
  "folderId": 0,
  "overwrite": true
}' | python3 -m json.tool
