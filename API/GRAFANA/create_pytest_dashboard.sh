#!/usr/bin/env bash
# Creates the pytest-clab-frr01 Results dashboard in Grafana via REST API.
# Uses Zabbix plugin schema 12 (required for v6.3.x).
# Run from the project root. Grafana must be running on http://localhost:5000.
# Credentials: admin/admin123

GRAFANA_URL="http://localhost:5000"
ZABBIX_DS_UID="efnqaelol143kc"
GRAFANA_USER="admin"
GRAFANA_PASS="admin123"

# Build a schema-12 Zabbix target block
zabbix_target() {
  local REF_ID="$1"
  local ITEM_FILTER="$2"
  cat <<ENDT
{
  "application": {"filter": ""},
  "countTriggersBy": "",
  "datasource": {"type": "alexanderzobnin-zabbix-datasource", "uid": "${ZABBIX_DS_UID}"},
  "evaltype": "0",
  "functions": [],
  "group": {"filter": "Pytest"},
  "host": {"filter": "containerlab-frr01"},
  "item": {"filter": "${ITEM_FILTER}"},
  "itemTag": {"filter": ""},
  "macro": {"filter": ""},
  "options": {
    "count": false,
    "disableDataAlignment": false,
    "showDisabledItems": false,
    "skipEmptyValues": false,
    "useTrends": "default",
    "useZabbixValueMapping": false
  },
  "proxy": {"filter": ""},
  "queryType": "0",
  "refId": "${REF_ID}",
  "resultFormat": "time_series",
  "schema": 12,
  "table": {"skipEmptyValues": false},
  "tags": {"filter": ""},
  "textFilter": "",
  "trigger": {"filter": ""}
}
ENDT
}

curl -s -u "${GRAFANA_USER}:${GRAFANA_PASS}" -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json

DS='${ZABBIX_DS_UID}'

def target(ref, item):
    return {
        'application':{'filter':''},
        'countTriggersBy':'',
        'datasource':{'type':'alexanderzobnin-zabbix-datasource','uid':DS},
        'evaltype':'0',
        'functions':[],
        'group':{'filter':'Pytest'},
        'host':{'filter':'containerlab-frr01'},
        'item':{'filter':item},
        'itemTag':{'filter':''},
        'macro':{'filter':''},
        'options':{'count':False,'disableDataAlignment':False,'showDisabledItems':False,'skipEmptyValues':False,'useTrends':'default','useZabbixValueMapping':False},
        'proxy':{'filter':''},
        'queryType':'0',
        'refId':ref,
        'resultFormat':'time_series',
        'schema':12,
        'table':{'skipEmptyValues':False},
        'tags':{'filter':''},
        'textFilter':'',
        'trigger':{'filter':''}
    }

db = {
  'uid':'pytest-clab-frr01',
  'title':'pytest-clab-frr01 Results',
  'tags':['pytest','containerlab','frr01'],
  'timezone':'browser',
  'schemaVersion':39,
  'refresh':'30s',
  'time':{'from':'now-3h','to':'now'},
  'panels':[
    {'id':1,'title':'Tests Passed','type':'stat','gridPos':{'h':6,'w':6,'x':0,'y':0},
     'options':{'reduceOptions':{'calcs':['lastNotNull']},'colorMode':'value','graphMode':'area','justifyMode':'center','textMode':'auto'},
     'fieldConfig':{'defaults':{'color':{'mode':'thresholds'},'thresholds':{'mode':'absolute','steps':[{'color':'red','value':None},{'color':'green','value':1}]},'unit':'short','noValue':'0'}},
     'datasource':{'uid':DS,'type':'alexanderzobnin-zabbix-datasource'},
     'targets':[target('A','pytest.tests_passed')]},
    {'id':2,'title':'Tests Failed','type':'stat','gridPos':{'h':6,'w':6,'x':6,'y':0},
     'options':{'reduceOptions':{'calcs':['lastNotNull']},'colorMode':'value','graphMode':'area','justifyMode':'center','textMode':'auto'},
     'fieldConfig':{'defaults':{'color':{'mode':'thresholds'},'thresholds':{'mode':'absolute','steps':[{'color':'green','value':None},{'color':'red','value':1}]},'unit':'short','noValue':'0'}},
     'datasource':{'uid':DS,'type':'alexanderzobnin-zabbix-datasource'},
     'targets':[target('A','pytest.tests_failed')]},
    {'id':3,'title':'Total Tests','type':'stat','gridPos':{'h':6,'w':6,'x':12,'y':0},
     'options':{'reduceOptions':{'calcs':['lastNotNull']},'colorMode':'value','graphMode':'area','justifyMode':'center','textMode':'auto'},
     'fieldConfig':{'defaults':{'color':{'fixedColor':'blue','mode':'fixed'},'unit':'short','noValue':'0'}},
     'datasource':{'uid':DS,'type':'alexanderzobnin-zabbix-datasource'},
     'targets':[target('A','pytest.tests_total')]},
    {'id':4,'title':'Exit Code (0=PASS)','type':'stat','gridPos':{'h':6,'w':6,'x':18,'y':0},
     'options':{'reduceOptions':{'calcs':['lastNotNull']},'colorMode':'background','graphMode':'none','justifyMode':'center','textMode':'auto'},
     'fieldConfig':{'defaults':{'color':{'mode':'thresholds'},'thresholds':{'mode':'absolute','steps':[{'color':'green','value':None},{'color':'red','value':1}]},'mappings':[{'options':{'0':{'text':'PASS'}},'type':'value'},{'options':{'from':1,'to':999,'result':{'text':'FAIL'}},'type':'range'}],'unit':'short','noValue':'0'}},
     'datasource':{'uid':DS,'type':'alexanderzobnin-zabbix-datasource'},
     'targets':[target('A','pytest.exit_code')]},
    {'id':5,'title':'Tests Passed / Failed Over Time','type':'timeseries','gridPos':{'h':9,'w':24,'x':0,'y':6},
     'fieldConfig':{'defaults':{'unit':'short','min':0,'custom':{'lineWidth':2,'fillOpacity':15}}},
     'datasource':{'uid':DS,'type':'alexanderzobnin-zabbix-datasource'},
     'targets':[target('A','pytest.tests_passed'),target('B','pytest.tests_failed')]}
  ]
}
print(json.dumps({'dashboard':db,'folderId':0,'overwrite':True}))
")" | python3 -m json.tool
