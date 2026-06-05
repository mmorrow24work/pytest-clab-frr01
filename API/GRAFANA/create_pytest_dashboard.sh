#!/usr/bin/env bash
# Creates the pytest-clab-frr01 Results dashboard in Grafana via REST API.
# Run from the project root. Grafana must be running on http://localhost:5000.
# Credentials: admin/admin (default — change as needed).

GRAFANA_URL="http://localhost:5000"
ZABBIX_DS_UID="efnqaelol143kc"

curl -s -u admin:admin -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -d '{
  "dashboard": {
    "uid": "pytest-clab-frr01",
    "title": "pytest-clab-frr01 Results",
    "tags": ["pytest", "containerlab", "frr01"],
    "timezone": "browser",
    "schemaVersion": 39,
    "refresh": "30s",
    "time": {"from": "now-2h", "to": "now"},
    "panels": [
      {
        "id": 1,
        "title": "Tests Passed",
        "type": "stat",
        "gridPos": {"h": 6, "w": 5, "x": 0, "y": 0},
        "options": {
          "reduceOptions": {"calcs": ["lastNotNull"]},
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "center",
          "textMode": "auto"
        },
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {"mode": "absolute", "steps": [{"color": "red","value": null},{"color": "green","value": 1}]},
            "unit": "short",
            "noValue": "0"
          }
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [{"refId":"A","group":{"filter":""},"host":{"filter":"containerlab-frr01"},"application":{"filter":""},"item":{"filter":"pytest.tests_passed"},"functions":[]}]
      },
      {
        "id": 2,
        "title": "Tests Failed",
        "type": "stat",
        "gridPos": {"h": 6, "w": 5, "x": 5, "y": 0},
        "options": {
          "reduceOptions": {"calcs": ["lastNotNull"]},
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "center",
          "textMode": "auto"
        },
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {"mode": "absolute", "steps": [{"color": "green","value": null},{"color": "red","value": 1}]},
            "unit": "short",
            "noValue": "0"
          }
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [{"refId":"A","group":{"filter":""},"host":{"filter":"containerlab-frr01"},"application":{"filter":""},"item":{"filter":"pytest.tests_failed"},"functions":[]}]
      },
      {
        "id": 3,
        "title": "Total Tests",
        "type": "stat",
        "gridPos": {"h": 6, "w": 5, "x": 10, "y": 0},
        "fieldConfig": {
          "defaults": {"color": {"fixedColor": "blue", "mode": "fixed"}, "unit": "short", "noValue": "0"}
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [{"refId":"A","group":{"filter":""},"host":{"filter":"containerlab-frr01"},"application":{"filter":""},"item":{"filter":"pytest.tests_total"},"functions":[]}]
      },
      {
        "id": 4,
        "title": "Exit Code (0=PASS)",
        "type": "stat",
        "gridPos": {"h": 6, "w": 5, "x": 15, "y": 0},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "background"},
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {"mode": "absolute", "steps": [{"color": "green","value": null},{"color": "red","value": 1}]},
            "mappings": [{"options":{"0":{"text":"PASS"}},"type":"value"},{"options":{"from":1,"to":999,"result":{"text":"FAIL"}},"type":"range"}],
            "unit": "short",
            "noValue": "0"
          }
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [{"refId":"A","group":{"filter":""},"host":{"filter":"containerlab-frr01"},"application":{"filter":""},"item":{"filter":"pytest.exit_code"},"functions":[]}]
      },
      {
        "id": 5,
        "title": "Tests Passed / Failed Over Time",
        "type": "timeseries",
        "gridPos": {"h": 9, "w": 24, "x": 0, "y": 6},
        "fieldConfig": {
          "defaults": {"unit": "short", "min": 0, "custom": {"lineWidth": 2, "fillOpacity": 15}}
        },
        "datasource": {"uid": "'"${ZABBIX_DS_UID}"'", "type": "alexanderzobnin-zabbix-datasource"},
        "targets": [
          {"refId":"A","group":{"filter":""},"host":{"filter":"containerlab-frr01"},"application":{"filter":""},"item":{"filter":"pytest.tests_passed"},"functions":[]},
          {"refId":"B","group":{"filter":""},"host":{"filter":"containerlab-frr01"},"application":{"filter":""},"item":{"filter":"pytest.tests_failed"},"functions":[]}
        ]
      }
    ]
  },
  "folderId": 0,
  "overwrite": true
}' | python3 -m json.tool
