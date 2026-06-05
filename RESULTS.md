# Results

---

## pytest HTML Report

![pytest HTML Report](SCREENSHOTS/pytest_report.png)

12 tests passed across the full sequence: connectivity → Zabbix host check → config backup → interface shutdown → VLAN LLD verification → Zabbix problem detection (40 s) → restore → problem clear.

---

## Grafana — pytest Results Dashboard

![Grafana pytest Results](SCREENSHOTS/grafana_pytest_results.png)

Dashboard UID: `pytest-clab-frr01` — Created via REST API (`API/GRAFANA/create_pytest_dashboard.sh`).  
Shows tests passed/failed counts and trend over time, backed by Zabbix items on the `containerlab-frr01` host.

---

## Grafana — Zabbix Host Status Dashboard

![Grafana Zabbix Dashboard](SCREENSHOTS/grafana_zabbix_hosts.png)

Dashboard UID: `clab-frr01-hosts` — Created via REST API (`API/GRAFANA/create_zabbix_hosts_dashboard.sh`).  
Shows eth0 and VLAN 100 interface traffic for all three routers, plus the latest pytest result.

---

## Test Run Summary

All runs used the full 10-test sequence. Loop ran continuously with a 5 s gap between passes.

| Run | Passed | Failed | Notes |
|---|---|---|---|
| Initial (part 1 - 6 tests) | 6 | 0 | Connectivity, Zabbix hosts, config backup |
| First full run | 10 | 2 | VLAN LLD not yet populated; Zabbix problem timeout |
| Full run after LLD forced | 12 | 0 | LLD forced via API (30 s interval), all green |
| Continuous loop run 1 | 12 | 0 | All green |
| Continuous loop run 2 | 12 | 0 | All green |
| Continuous loop run 3 | 12 | 0 | All green |
| Continuous loop run 4 | 12 | 0 | All green |

### Duration
- Single full run: **~2 minutes** (dominated by the 40 s Zabbix problem detection wait)
- Loop interval: 5 s between runs

---

## Key Observations

- **Zabbix LLD (test_08)** fails on first start because the default LLD interval is 1 hour. Use `API/ZABBIX/force_lld.sh` or reduce the interval temporarily to get results immediately.
- **Zabbix problem detection (test_09)** requires the interface to be monitored via LLD-discovered items. Once LLD runs, the trigger fires within ~40 s of the interface going down.
- **test_12 (problem cleared after restore)** passes on the first run — Zabbix clears the `Link down` problem as soon as the interface comes back up and the next agent check runs.
