#!/usr/bin/env bash
# Creates the clab frr01 Zabbix Host Status dashboard in Grafana via REST API.
# Uses Zabbix plugin schema-12 format (required for v6.3.x).
# Grafana: http://localhost:5000  Credentials: admin/admin123

GRAFANA_URL="http://localhost:5000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin123"

curl -s -u "${GRAFANA_USER}:${GRAFANA_PASS}" -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -d "$(python3 - << 'PYEOF'
import json

DS = "efnqaelol143kc"
GRP_NODES  = "Linux servers"   # group containing router1/2/3, PC1/2/3
GRP_PYTEST = "Pytest"          # group containing containerlab-frr01

def t(ref, host, item, group=GRP_NODES):
    return {
        "application":{"filter":""},"countTriggersBy":"",
        "datasource":{"type":"alexanderzobnin-zabbix-datasource","uid":DS},
        "evaltype":"0","functions":[],
        "group":{"filter":group},
        "host":{"filter":host},
        "item":{"filter":item},
        "itemTag":{"filter":""},"macro":{"filter":""},
        "options":{"count":False,"disableDataAlignment":False,"showDisabledItems":False,
                   "skipEmptyValues":False,"useTrends":"default","useZabbixValueMapping":False},
        "proxy":{"filter":""},"queryType":"0","refId":ref,
        "resultFormat":"time_series","schema":12,
        "table":{"skipEmptyValues":False},"tags":{"filter":""},
        "textFilter":"","trigger":{"filter":""}
    }

def ts(id_, title, targets, x, y, w=12, h=8):
    return {
        "id":id_,"title":title,"type":"timeseries",
        "gridPos":{"h":h,"w":w,"x":x,"y":y},
        "fieldConfig":{"defaults":{
            "unit":"bps","min":0,
            "color":{"mode":"palette-classic"},
            "custom":{"lineWidth":2,"fillOpacity":10}
        }},
        "datasource":{"uid":DS,"type":"alexanderzobnin-zabbix-datasource"},
        "targets":targets
    }

def stat(id_, title, host, item, x, y, w=8, h=6, group=GRP_PYTEST,
         calc="lastNotNull", color_mode="value", steps=None, fixed_color=None,
         unit="short", mappings=None, no_value="0"):
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
        "targets":[t("A", host, item, group=group)],
    }
    if mappings:
        cfg["fieldConfig"]["defaults"]["mappings"] = mappings
    return cfg

GR = [{"color":"red","value":None},{"color":"green","value":1}]
RG = [{"color":"green","value":None},{"color":"red","value":1}]
PM = [{"options":{"0":{"text":"PASS","color":"green"}},"type":"value"},
      {"options":{"from":1,"to":999,"result":{"text":"FAIL","color":"red"}},"type":"range"}]

panels = [
    # Row 0 (y=0): Management — eth0 all 6 clab hosts
    ts(1, "All Hosts — eth0 Bits Received",
       [t("A", "/.*/", "Interface eth0: Bits received")],
       0, 0),
    ts(2, "All Hosts — eth0 Bits Sent",
       [t("A", "/.*/", "Interface eth0: Bits sent")],
       12, 0),

    # Row 1 (y=8): Routers — VLAN 100 sub-interfaces (eth1.100 / eth2.100 / eth3.100)
    ts(3, "Routers — VLAN 100 Sub-interfaces Bits Received",
       [t("A", "/router.*/", "/Interface eth.*100.*Bits received/")],
       0, 8),
    ts(4, "Routers — VLAN 100 Sub-interfaces Bits Sent",
       [t("A", "/router.*/", "/Interface eth.*100.*Bits sent/")],
       12, 8),

    # Row 2 (y=16): Routers — br100 bridge (aggregated VLAN 100 traffic)
    ts(5, "Routers — br100 Bridge Bits Received",
       [t("A", "/router.*/", "Interface br100: Bits received")],
       0, 16),
    ts(6, "Routers — br100 Bridge Bits Sent",
       [t("A", "/router.*/", "Interface br100: Bits sent")],
       12, 16),

    # Row 3 (y=24): Routers — trunk uplinks (eth1 / eth2 / eth3, untagged)
    ts(7, "Routers — Trunk Uplinks Bits Received",
       [t("A", "/router.*/", "/Interface eth[123]: Bits received/")],
       0, 24),
    ts(8, "Routers — Trunk Uplinks Bits Sent",
       [t("A", "/router.*/", "/Interface eth[123]: Bits sent/")],
       12, 24),

    # Row 4 (y=32): PCs — eth1.100 and eth1 trunk
    ts(9, "PCs — eth1.100 Bits Received",
       [t("A", "/PC.*/", "Interface eth1.100: Bits received")],
       0, 32),
    ts(10, "PCs — eth1.100 Bits Sent",
       [t("A", "/PC.*/", "Interface eth1.100: Bits sent")],
       12, 32),

    # Row 5 (y=40): pytest last-run stats
    stat(11, "pytest — Last Run Passed",
         "containerlab-frr01", "pytest.tests_passed", 0, 40, steps=GR),
    stat(12, "pytest — Last Run Failed",
         "containerlab-frr01", "pytest.tests_failed", 8, 40, steps=RG),
    stat(13, "pytest — Last Exit Code",
         "containerlab-frr01", "pytest.exit_code",    16, 40,
         color_mode="background",
         steps=[{"color":"green","value":None},{"color":"red","value":1}],
         mappings=PM),
]

db = {
    "uid":"clab-frr01-hosts","title":"clab frr01 — Zabbix Host Status",
    "tags":["zabbix","containerlab","frr01"],"timezone":"browser",
    "schemaVersion":39,"refresh":"30s","time":{"from":"now-3h","to":"now"},
    "panels":panels
}

print(json.dumps({"dashboard":db,"folderId":0,"overwrite":True}))
PYEOF
)" | python3 -m json.tool
