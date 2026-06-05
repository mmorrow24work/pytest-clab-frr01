# Quick Start

## Prerequisites

- Docker + Docker Compose
- [containerlab](https://containerlab.dev/) (`clab`)
- Python 3.12
- Zabbix docker-compose stack cloned to `~/git/zabbix-docker/`
- `~/git/digital-twin-containerlab/` repo (provides Zabbix compose overrides)
- The `digital-twin` Docker bridge network must exist before starting Zabbix

## 1 — Create the digital-twin network (first time only)

```bash
docker network create digital-twin
```

## 2 — Start Zabbix

```bash
cp ~/git/digital-twin-containerlab/zabbix_docker_compose/* ~/git/zabbix-docker/.
cd ~/git/zabbix-docker/
docker compose \
  -f ./docker-compose_v3_alpine_mysql_snmptraps_latest.yaml \
  -f ./docker-compose.override.yml \
  up -d
```

Wait ~60 s for MySQL to initialise. Zabbix web UI: **http://localhost** (Admin / zabbix).

## 3 — Generate a Zabbix API token

1. Log in to Zabbix → Administration → API tokens → Create
2. Copy the token into the project root:

```bash
echo "<your-token>" > ~/git/pytest-clab-frr01/zabbix_token.txt
```

The file is excluded from git (`.gitignore`).

## 4 — Deploy the frr01 clab network

```bash
cd ~/git/containerlab/lab-examples/frr01
./run.sh
```

`run.sh` runs `clab deploy --topo frr01.clab.yml` then `./PC-interfaces.sh` to configure the VLAN 100 sub-interfaces on the Alpine PC containers.

## 5 — Confirm Zabbix hosts for the clab nodes

The six clab nodes register themselves with Zabbix automatically via the Zabbix agent. Confirm all six appear in Zabbix (Monitoring → Hosts) with status **Enabled** and agent checks returning data:

| Zabbix visible name | IP address | Agent port |
|---|---|---|
| router1 | 172.18.0.41 | 10050 |
| router2 | 172.18.0.42 | 10050 |
| router3 | 172.18.0.43 | 10050 |
| PC1 | 172.18.0.44 | 10050 |
| PC2 | 172.18.0.45 | 10050 |
| PC3 | 172.18.0.46 | 10050 |

If hosts are missing, verify the `digital-twin` Docker network exists and the containers are running (`docker ps`).

## 5a — Force LLD to run immediately (required after every fresh Zabbix start)

Zabbix LLD (Link-Layer Discovery) defaults to a 1-hour interval. Tests `test_08` and `test_09` both depend on LLD having discovered the `eth1.100` sub-interfaces. Run the force script once after starting Zabbix — it temporarily reduces the LLD interval to 30 s, waits 75 s, then restores it to 1 h:

```bash
bash ~/git/pytest-clab-frr01/API/ZABBIX/force_lld.sh
```

Wait for the script to complete (~75 s) before running tests.

## 6 — Activate the virtual environment

```bash
source ~/git/pytest-virtual-environment/.venv/bin/activate
```

### Python packages in the virtual environment

| Package | Version |
|---|---|
| bcrypt | 5.0.0 |
| certifi | 2026.5.20 |
| cffi | 2.0.0 |
| charset-normalizer | 3.4.7 |
| cryptography | 48.0.0 |
| idna | 3.18 |
| iniconfig | 2.3.0 |
| invoke | 3.0.3 |
| Jinja2 | 3.1.6 |
| markdown-it-py | 4.2.0 |
| MarkupSafe | 3.0.3 |
| mdurl | 0.1.2 |
| packaging | 26.2 |
| paramiko | 5.0.0 |
| pip | 26.1.2 |
| pluggy | 1.6.0 |
| pycparser | 3.0 |
| Pygments | 2.20.0 |
| PyNaCl | 1.6.2 |
| pytest | 9.0.3 |
| pytest-html | 4.2.0 |
| pytest-metadata | 3.1.1 |
| PyYAML | 6.0.3 |
| requests | 2.34.2 |
| rich | 15.0.0 |
| urllib3 | 2.7.0 |

**Notable differences from a minimal pytest install:**  
`paramiko` and `cryptography` packages are included for SSH-based testing (not used in the current suite but available). `invoke` is included for task automation. `rich` provides colourised CLI output.

## 7 — Create the Grafana dashboards

Run both API scripts once to provision the dashboards (Grafana must be running):

```bash
bash ~/git/pytest-clab-frr01/API/GRAFANA/create_pytest_dashboard.sh
bash ~/git/pytest-clab-frr01/API/GRAFANA/create_zabbix_hosts_dashboard.sh
```

Dashboards are available at **http://localhost:5000** (admin / admin123):

| Dashboard | UID | Description |
|---|---|---|
| pytest-clab-frr01 Results | `pytest-clab-frr01` | Cumulative pass/fail counts, run count, avg/max duration |
| clab frr01 — Zabbix Host Status | `clab-frr01-hosts` | Interface traffic for all 6 hosts across all interface types |

## 8 — Run the tests

Tests must run from the clab lab directory because `helpers.py` uses relative paths for `frr01.clab.yml`, `backups/`, and `zabbix_token.txt`:

```bash
cd ~/git/containerlab/lab-examples/frr01
/home/mickm/git/pytest-virtual-environment/.venv/bin/pytest \
  -v -s --tb=short \
  --html=~/git/pytest-clab-frr01/reports/report.html --self-contained-html \
  ~/git/pytest-clab-frr01/tests/
```

HTML results are written to `~/git/pytest-clab-frr01/reports/report.html`.

## 9 — Run continuously (loop mode)

The continuous loop runs the full suite repeatedly, pushing metrics to Zabbix after each run:

```bash
bash ~/git/pytest-clab-frr01/tests/run_continuous.sh
```

Press `Ctrl-C` to stop. Metrics (tests_passed, tests_failed, tests_total, exit_code, run_duration_seconds) are sent to the `containerlab-frr01` Zabbix host after each run and appear in the pytest-clab-frr01 Grafana dashboard.

## 11 — Stop Zabbix

```bash
cd ~/git/zabbix-docker/
docker compose \
  -f docker-compose_v3_alpine_mysql_snmptraps_latest.yaml \
  -f ./docker-compose.override.yml \
  down
```

## 12 — Destroy the clab network

```bash
cd ~/git/containerlab/lab-examples/frr01
clab destroy -t ./frr01.clab.yml
```
