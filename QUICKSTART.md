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

The run script deploys the topology and waits for containers to be healthy.

## 5 — Create Zabbix hosts for the clab nodes

Add the following hosts manually in Zabbix (Monitoring → Hosts → Create) or via the API:

| Zabbix host name | IP address | Agent port | Templates |
|---|---|---|---|
| router1 | 172.18.0.41 | 10050 | Linux by Zabbix agent |
| router2 | 172.18.0.42 | 10050 | Linux by Zabbix agent |
| router3 | 172.18.0.43 | 10050 | Linux by Zabbix agent |
| PC1 | 172.18.0.44 | 10050 | Linux by Zabbix agent |
| PC2 | 172.18.0.45 | 10050 | Linux by Zabbix agent |
| PC3 | 172.18.0.46 | 10050 | Linux by Zabbix agent |

Enable LLD rules for **Network interfaces** on all hosts to discover `eth0`, `eth1.100`, etc.

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

## 7 — Run the tests

```bash
cd ~/git/pytest-clab-frr01
pytest -v --html=reports/report.html --self-contained-html -s
```

HTML results are written to `reports/report.html`.

## 8 — Run continuously (loop mode)

```bash
cd ~/git/pytest-clab-frr01
bash tests/loop-wrapper-frr01.sh
```

## 9 — Stop Zabbix

```bash
cd ~/git/zabbix-docker/
docker compose \
  -f docker-compose_v3_alpine_mysql_snmptraps_latest.yaml \
  -f ~/git/digital-twin-containerlab/zabbix_docker_compose/docker-compose.override.yml \
  down
```

## 10 — Destroy the clab network

```bash
cd ~/git/containerlab/lab-examples/frr01
clab destroy -t ./frr01.clab.yml
```
