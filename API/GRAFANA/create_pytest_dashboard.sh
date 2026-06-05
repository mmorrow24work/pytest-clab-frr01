#!/usr/bin/env bash
# Creates the pytest-clab-frr01 Results dashboard in Grafana via REST API.
# Uses Zabbix plugin schema 12 (required for v6.3.x).
# Grafana: http://localhost:5000  Credentials: admin/admin123

GRAFANA_URL="http://localhost:5000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin123"

curl -s -u "${GRAFANA_USER}:${GRAFANA_PASS}" -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -d "$(python3 - << 'PYEOF'
import json

DS = "efnqaelol143kc"

def t(ref, item):
    return {
        "application":{"filter":""},"countTriggersBy":"",
        "datasource":{"type":"alexanderzobnin-zabbix-datasource","uid":DS},
        "evaltype":"0","functions":[],
        "group":{"filter":"Pytest"},
        "host":{"filter":"containerlab-frr01"},
        "item":{"filter":item},
        "itemTag":{"filter":""},"macro":{"filter":""},
        "options":{"count":False,"disableDataAlignment":False,"showDisabledItems":False,
                   "skipEmptyValues":False,"useTrends":"default","useZabbixValueMapping":False},
        "proxy":{"filter":""},"queryType":"0","refId":ref,
        "resultFormat":"time_series","schema":12,
        "table":{"skipEmptyValues":False},"tags":{"filter":""},
        "textFilter":"","trigger":{"filter":""}
    }

def stat(id_, title, item, x, y, w=6, h=6, calc="lastNotNull",
         color_mode="value", steps=None, fixed_color=None, unit="short",
         mappings=None, no_value="0"):
    cfg = {
        "id":id_,"title":title,"type":"stat",
        "gridPos":{"h":h,"w":w,"x":x,"y":y},
        "options":{"reduceOptions":{"calcs":[calc]},"colorMode":color_mode,
                   "graphMode":"area","justifyMode":"center","textMode":"auto"},
        "fieldConfig":{"defaults":{
            "color":{"fixedColor":fixed_color,"mode":"fixed"} if fixed_color else {"mode":"thresholds"},
            "unit":unit,"noValue":no_value,
            "thresholds":{"mode":"absolute","steps":steps or []}}},
        "datasource":{"uid":DS,"type":"alexanderzobnin-zabbix-datasource"},
        "targets":[t("A",item)],
    }
    if mappings:
        cfg["fieldConfig"]["defaults"]["mappings"] = mappings
    return cfg

GR = [{"color":"red","value":None},{"color":"green","value":1}]
RG = [{"color":"green","value":None},{"color":"red","value":1}]
PM = [{"options":{"0":{"text":"PASS","color":"green"}},"type":"value"},
      {"options":{"from":1,"to":999,"result":{"text":"FAIL","color":"red"}},"type":"range"}]

db = {
  "uid":"pytest-clab-frr01","title":"pytest-clab-frr01 Results",
  "tags":["pytest","containerlab","frr01"],"timezone":"browser",
  "schemaVersion":39,"refresh":"30s","time":{"from":"now-3h","to":"now"},
  "panels":[
    stat(1,"Total Tests Run (cumulative)","pytest.tests_passed",0,0,calc="sum",fixed_color="blue"),
    stat(2,"Cumulative Tests Passed","pytest.tests_passed",6,0,calc="sum",steps=GR),
    stat(3,"Cumulative Tests Failed","pytest.tests_failed",12,0,calc="sum",steps=RG),
    stat(4,"Number of Runs","pytest.tests_total",18,0,calc="count",fixed_color="purple"),
    stat(5,"Last Run — Passed","pytest.tests_passed",0,6,w=5,steps=GR),
    stat(6,"Last Run — Failed","pytest.tests_failed",5,6,w=5,steps=RG),
    stat(7,"Last Run — Exit Code","pytest.exit_code",10,6,w=4,color_mode="background",
         steps=[{"color":"green","value":None},{"color":"red","value":1}],mappings=PM),
    stat(8,"Avg Run Duration","pytest.run_duration_seconds",14,6,w=5,calc="mean",
         fixed_color="orange",unit="s",no_value="N/A"),
    stat(9,"Max Run Duration","pytest.run_duration_seconds",19,6,w=5,calc="max",
         fixed_color="yellow",unit="s",no_value="N/A"),
    {"id":10,"title":"Tests Passed / Failed Over Time","type":"timeseries",
     "gridPos":{"h":9,"w":16,"x":0,"y":12},
     "fieldConfig":{"defaults":{"unit":"short","min":0,"custom":{"lineWidth":2,"fillOpacity":15}}},
     "datasource":{"uid":DS,"type":"alexanderzobnin-zabbix-datasource"},
     "targets":[t("A","pytest.tests_passed"),t("B","pytest.tests_failed")]},
    {"id":11,"title":"Run Duration (seconds)","type":"timeseries",
     "gridPos":{"h":9,"w":8,"x":16,"y":12},
     "fieldConfig":{"defaults":{"unit":"s","min":0,
                                "color":{"fixedColor":"orange","mode":"fixed"},
                                "custom":{"lineWidth":2,"fillOpacity":10}}},
     "datasource":{"uid":DS,"type":"alexanderzobnin-zabbix-datasource"},
     "targets":[t("A","pytest.run_duration_seconds")]},
  ]
}

print(json.dumps({"dashboard":db,"folderId":0,"overwrite":True}))
PYEOF
)" | python3 -m json.tool
