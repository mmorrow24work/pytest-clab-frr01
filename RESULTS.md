# Results

---

## pytest HTML Report

![pytest HTML Report](SCREENSHOTS/pytest_report.png)

12 tests passed across the full sequence: connectivity → Zabbix host check → config backup → interface shutdown → VLAN LLD verification → Zabbix problem detection (40 s) → restore → problem clear.

---

## Grafana — pytest Results Dashboard

![Grafana pytest Results](SCREENSHOTS/grafana_pytest_results.png)

Dashboard UID: `pytest-clab-frr01` — Created via REST API (`API/GRAFANA/create_pytest_dashboard.sh`).  
Shows tests passed/failed counts and trend over time, backed by Zabbix trapper items on the `containerlab-frr01` host.

---

## Grafana — Zabbix Host Status Dashboard

![Grafana Zabbix Dashboard](SCREENSHOTS/grafana_zabbix_hosts.png)

Dashboard UID: `clab-frr01-hosts` — Created via REST API (`API/GRAFANA/create_zabbix_hosts_dashboard.sh`).  
Shows eth0 and VLAN 100 interface traffic for all three routers, plus the latest pytest result.

---

## Continuous Loop Sweep Results

34 consecutive runs completed before testing was stopped. All 12/12 tests passed on every run.

| Run | Timestamp (BST) | Passed | Failed |
|---|---|---|---|
| 1 | 13:54:45 | 12 | 0 |
| 2 | 13:55:10 | 12 | 0 |
| 3 | 13:55:37 | 12 | 0 |
| 4 | 13:56:02 | 12 | 0 |
| 5 | 13:56:27 | 12 | 0 |
| 6–34 | 13:58–14:12 | 12 | 0 |

**Total: 34 runs × 12 tests = 408 test executions — 0 failures.**

### Duration
- Single full run: **~2 minutes** (40 s Zabbix problem detection + 40 s clear wait dominates)
- Loop interval: 5 s between runs
- Total sweep: **~20 minutes**

---

## Setup Issues Encountered

### 1. Zabbix LLD defaults to 1h interval
After a fresh Zabbix start, `test_08` (VLAN LLD check) failed because LLD hadn't run yet.  
**Fix:** Forced LLD to run immediately using `API/ZABBIX/force_lld.sh` (temporarily sets interval to 30 s, waits 75 s, restores to 1 h).  
This only needs to be done once per fresh Zabbix start.

### 2. Zabbix problem detection requires LLD to have run first
`test_09` (interface down → Zabbix PROBLEM) failed on the first attempt because the `eth1.100` LLD item didn't exist yet — no item, no trigger.  
**Fix:** Same as above — force LLD first, then run the full test suite.

### 3. Virtual environment path differs from task description
Tasks referenced `~/git/pytest-virtual-environment/bin/activate` but the actual path is  
`~/git/pytest-virtual-environment/.venv/bin/activate`.

### 4. Tests must run from the clab lab directory
`helpers.py` uses relative paths for `frr01.clab.yml`, `backups/`, and `zabbix_token.txt`.  
Always `cd /home/mickm/git/containerlab/lab-examples/frr01` before running pytest.
