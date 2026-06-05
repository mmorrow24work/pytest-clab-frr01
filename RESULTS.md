# Results

---

## EXTRAS Test Suite — iperf3 Throughput Results

All measured on Docker veth links on a single Linux host (WSL2). Values are consistent across runs.

| Test | Path | Throughput |
|---|---|---|
| PC1→PC2 (OSPF data plane) | eth1 192.168.11.2 → 192.168.12.2 | ~11.5 Gbps |
| PC2→PC3 (OSPF data plane) | eth1 192.168.12.2 → 192.168.13.2 | ~11.3 Gbps |
| Backbone r1→r2 | 192.168.1.1 → 192.168.1.2 | ~19.5 Gbps |
| Backbone r1→r3 | 192.168.1.1 → 192.168.2.2 | ~19.2 Gbps |
| Backbone r2→r3 | 192.168.3.1 → 192.168.3.2 | ~19.5 Gbps |
| VLAN100 PC1→PC2 | eth1.100 192.168.100.1 → 192.168.100.2 | ~7.5 Gbps |
| VLAN100 PC1→router1 br100 | eth1.100 → 192.168.100.10 | ~16 Gbps |
| Parallel 4-stream PC1→PC2 | 4× streams | ~29 Gbps aggregate |
| Reverse PC2→PC1 | `-R` flag | ~11.5 Gbps |

**Minimum threshold:** 1 Gbps — all tests pass with headroom ≥ 7×.

---

## EXTRAS Test Suite — SNMP Trap Results

All traps verified via `docker logs --since` on the `zabbix-docker-zabbix-snmptraps-1` container.

| Test | Trap | Source | Result |
|---|---|---|---|
| test_18 | coldStart | router1 | Received in snmptrapd within 15 s |
| test_19 | warmStart (concurrent) | router1, router2, router3 | All 3 received within 20 s |
| test_20 | linkDown + varbinds | router2 | OID and varbinds preserved in log |
| test_21 | coldStart + sysDescr sentinel | router3 | Unique string preserved verbatim |
| test_22 | Zabbix infra + coldStart | router1 | SNMP interface + item confirmed via API; trap delivery verified |

**Note:** The Zabbix snmptrapd container has a busybox `date` format bug that prevents `snmptraps.log` from being written. Traps are received correctly and appear in `docker logs`. The file-based Zabbix history integration is advisory (see Problems Encountered in README.md).

---

## pytest HTML Report

![pytest HTML Report](SCREENSHOTS/pytest_report.png)

12 tests passed across the full sequence: connectivity → Zabbix host check → config backup → interface shutdown → VLAN LLD verification → Zabbix problem detection (40 s) → restore → problem clear.

---

## Grafana — pytest Results Dashboard

![Grafana pytest Results](SCREENSHOTS/grafana_pytest_results.png)

Dashboard UID: `pytest-clab-frr01` — Created via REST API (`API/GRAFANA/create_pytest_dashboard.sh`).  
Shows cumulative tests passed/failed, run count, avg/max run duration, and a time-series trend. Backed by Zabbix trapper items on the `containerlab-frr01` host.  
Screenshot shows the EXTRAS 30-minute loop: **442 total executions, 17 runs, 26 tests/run, 0 failures, avg 1.76 min/run.**

---

## Grafana — Zabbix Host Status Dashboard

![Grafana Zabbix Dashboard](SCREENSHOTS/grafana_zabbix_hosts.png)

Dashboard UID: `clab-frr01-hosts` — Created via REST API (`API/GRAFANA/create_zabbix_hosts_dashboard.sh`).  
Shows interface traffic for all 6 clab hosts across every interface type:

| Row | Panels |
|---|---|
| Management | eth0 Bits Received / Sent — all 6 hosts (routers + PCs) |
| VLAN 100 sub-interfaces | eth1.100 / eth2.100 / eth3.100 Received / Sent — all 3 routers |
| Bridge | br100 Received / Sent — all 3 routers |
| Trunk uplinks | eth1 / eth2 / eth3 Received / Sent — all 3 routers |
| PCs | eth1.100 Received / Sent — PC1 / PC2 / PC3 |
| pytest | Last Run Passed / Failed / Exit Code |

---

## Continuous Loop Sweep Results

### Core tests (`tests/run_continuous.sh`) — 10 tests per run

35 runs completed. All 12/12 tests passed on every run.

| Run | Timestamp (BST) | Passed | Failed |
|---|---|---|---|
| 1 (manual) | ~13:53 | 12 | 0 |
| 2 | 13:54:45 | 12 | 0 |
| 3 | 13:55:10 | 12 | 0 |
| 4 | 13:55:37 | 12 | 0 |
| 5 | 13:56:02 | 12 | 0 |
| 6–35 | 13:58–14:12 | 12 | 0 |

**Total: 35 runs × 12 tests = 420 test executions — 0 failures.**

#### Duration
- Average run duration: **~28 s** (as recorded in `pytest.run_duration_seconds` Zabbix item)
- Maximum run duration: **~2.2 minutes** (Zabbix problem detection + clear wait dominates)
- Loop interval: 5 s between runs
- Total sweep: **~20 minutes**

---

### EXTRAS loop (`EXTRAS/run_loop.sh`) — 26 tests per run (core + EXTRAS)

17 runs completed over 30 minutes (16:29–16:59 BST). All 26/26 tests passed on every run.

| Run | Timestamp (BST) | Passed | Failed |
|---|---|---|---|
| 1 | 16:29 | 26 | 0 |
| 2–8 | 16:31–16:43 | 26 | 0 |
| 9–16 | 16:44–16:56 | 26 | 0 |
| 17 | 16:57 | 26 | 0 |

**Total: 17 runs × 26 tests = 442 test executions — 0 failures.**

#### Duration
- Average run duration: **1.76 minutes** (Grafana stat — includes 5 iperf3 tests + 5 SNMP trap tests)
- Maximum run duration: **3.23 minutes** (Zabbix problem detection + SNMP trap waits combined)
- Loop interval: 5 s between runs
- Total sweep: **30 minutes**

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
