import subprocess
import json
import time
import requests
import re
from pathlib import Path

# Optional: used for parsing .clab.yml intent automatically.
# Install if missing: pip install pyyaml
try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover
    yaml = None

ROUTERS = [
    "clab-frr01-router1",
    "clab-frr01-router2",
    "clab-frr01-router3",
]

PCS = [
    "clab-frr01-PC1",
    "clab-frr01-PC2",
    "clab-frr01-PC3",
]

ALL_NODES = ROUTERS + PCS

# Default topology file for this lab directory
CLAB_TOPO_FILE = "frr01.clab.yml"

# -------------------------
# SNMP TRAP constants
# -------------------------

# IP of the zabbix-snmptraps container on the digital-twin Docker network.
# Containers send traps to this IP:port; snmptrapd writes to SNMPTRAP_LOG.
SNMPTRAP_CONTAINER = "zabbix-docker-zabbix-snmptraps-1"
SNMPTRAP_IP        = "172.18.0.5"
SNMPTRAP_PORT      = "1162"
SNMPTRAP_LOG       = "/var/lib/zabbix/snmptraps/snmptraps.log"

# Management IP of each frr01 node (used to match source in snmptraps.log)
NODE_MGMT_IP = {
    "clab-frr01-router1": "172.18.0.41",
    "clab-frr01-router2": "172.18.0.42",
    "clab-frr01-router3": "172.18.0.43",
    "clab-frr01-PC1":     "172.18.0.51",
    "clab-frr01-PC2":     "172.18.0.52",
    "clab-frr01-PC3":     "172.18.0.53",
}

# Data-plane IPs used by iperf tests
IPERF_IPS = {
    # eth1 (PC↔router access links)
    "clab-frr01-PC1":     "192.168.11.2",
    "clab-frr01-PC2":     "192.168.12.2",
    "clab-frr01-PC3":     "192.168.13.2",
    # backbone links: peer IP reachable from each router
    "clab-frr01-router1": "192.168.1.1",
    "clab-frr01-router2": "192.168.1.2",
    "clab-frr01-router3": "192.168.2.2",
    # VLAN 100 bridge IPs
    "PC1_vlan100":     "192.168.100.1",
    "PC2_vlan100":     "192.168.100.2",
    "PC3_vlan100":     "192.168.100.3",
    "router1_br100":   "192.168.100.10",
    "router2_br100":   "192.168.100.20",
    "router3_br100":   "192.168.100.30",
}

# -------------------------
# iperf3 helpers
# -------------------------

def iperf_run(server_container, client_container, server_ip,
              duration=5, parallel=1, reverse=False, port=5201):
    """Start a one-shot iperf3 server on server_container, run a client from
    client_container, and return the received throughput in Mbps.

    Uses --one-off so the server exits automatically after one connection.
    """
    # Kill any stale iperf3 first
    subprocess.run(
        ["docker", "exec", server_container, "sh", "-c", "pkill -9 iperf3 2>/dev/null; true"],
        capture_output=True,
    )
    time.sleep(0.2)

    subprocess.Popen(
        ["docker", "exec", "-d", server_container,
         "iperf3", "-s", "--one-off", "-p", str(port)],
    )
    time.sleep(0.5)

    cmd = [
        "docker", "exec", client_container,
        "iperf3", "-c", server_ip, "-p", str(port),
        "-t", str(duration), "--json",
    ]
    if parallel > 1:
        cmd += ["-P", str(parallel)]
    if reverse:
        cmd.append("-R")

    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=duration + 20)
    if result.returncode != 0:
        raise RuntimeError(
            f"iperf3 client failed (rc={result.returncode}): {result.stderr.strip()}"
        )

    data = json.loads(result.stdout)
    # sum_received covers multi-stream; fall back to first stream for single
    end = data["end"]
    if "sum_received" in end:
        bps = end["sum_received"]["bits_per_second"]
    else:
        bps = end["streams"][0]["receiver"]["bits_per_second"]
    return bps / 1e6   # → Mbps


# -------------------------
# SNMP trap helpers
# -------------------------

def snmptraps_log_size():
    """Return a Unix timestamp to use as a 'before' marker for trap checks.

    Named log_size for API compatibility; actually returns time.time() because
    the Zabbix snmptrapd container logs to stdout (docker logs) rather than
    writing to the snmptraps.log file (busybox date format bug in the handler
    prevents the file from being updated).
    """
    return time.time()


def snmp_trap_send(source_container, oid="SNMPv2-MIB::coldStart.0",
                   community="public", extra_varbinds=None):
    """Send an SNMPv2c trap from source_container to Zabbix snmptrapd."""
    cmd = [
        "docker", "exec", source_container,
        "snmptrap", "-v", "2c", "-c", community,
        f"{SNMPTRAP_IP}:{SNMPTRAP_PORT}",
        "",  # sysUpTime (leave empty for auto)
        oid,
    ]
    if extra_varbinds:
        cmd += extra_varbinds
    subprocess.run(cmd, check=True, capture_output=True)


def snmptrap_wait_for(source_ip, before_ts, oid_substring="", timeout=15):
    """Poll docker logs of the snmptrap container for a new entry from source_ip.

    before_ts is a Unix timestamp (float) returned by snmptraps_log_size() —
    used as the --since argument to 'docker logs'.

    Returns (True, snippet) if found within timeout, else (False, "").
    """
    import datetime
    # Format as RFC3339 UTC for docker logs --since
    since = datetime.datetime.utcfromtimestamp(before_ts - 1).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(
            ["docker", "logs", "--since", since, SNMPTRAP_CONTAINER],
            capture_output=True, text=True,
        )
        # snmptrapd writes to stdout; docker may put daemon msgs on stderr
        logs = result.stdout + result.stderr
        if source_ip in logs:
            if not oid_substring or oid_substring in logs:
                lines = logs.split("\n")
                snippet_lines: list[str] = []
                for i, line in enumerate(lines):
                    if source_ip in line:
                        snippet_lines = lines[i: i + 4]
                        break
                return True, "\n".join(snippet_lines)
        time.sleep(1)
    return False, ""


def run_cmd(cmd):
    """Backward-compatible: return stdout as string."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def run_cmd_full(cmd):
    """Return (stdout, stderr, rc) for diagnostics."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def docker_exec(container, command):
    """Backward-compatible: return stdout as string."""
    cmd = f"docker exec {container} sh -c '{command}'"
    return run_cmd(cmd)

def docker_exec_full(container, command):
    """Return (stdout, stderr, rc) for diagnostics."""
    cmd = f"docker exec {container} sh -c '{command}'"
    return run_cmd_full(cmd)



def interface_is_up(container, interface):
    output = docker_exec(
        container,
        f"ip link show {interface}"
    )

    return "UP" in output


def backup_frr_config(container):
    output = docker_exec(
        container,
        "cat /etc/frr/frr.conf"
    )

    filename = f"backups/{container}.conf"

    with open(filename, "w") as f:
        f.write(output)

    return filename


def shutdown_interface(container, interface):
    docker_exec(
        container,
        f"ip link set {interface} down"
    )


def start_iperf_server():
    docker_exec(
        "clab-frr01-PC3",
        "pkill iperf3 || true"
    )

    # Use shell quoting for redirects
    docker_exec(
        "clab-frr01-PC3",
        "sh -c 'nohup iperf3 -s > /tmp/iperf.log 2>&1 &'"
    )



def run_iperf_client():
    stdout, stderr, rc = docker_exec_full(
        "clab-frr01-router1",
        "iperf3 -c 192.168.100.3 -t 5"
    )
    # Return combined text so tests can see why it failed
    return (stdout + "\n" + stderr).strip()


def get_interface_counters(container, interface):
    output = docker_exec(
        container,
        f"cat /sys/class/net/{interface}/statistics/rx_bytes"
    )

    return int(output)

def zabbix_get_problems(hostids=None, recent=True):
    params = {
        "output": ["eventid", "name", "severity", "clock"],
        "sortfield": ["eventid"],
        "sortorder": "DESC",
        "recent": recent,
    }

    if hostids is not None:
        params["hostids"] = hostids

    return zabbix_api("problem.get", params)

def zabbix_find_interface_problem(hostname, interface):
    # Resolve hostname -> numeric hostid
    hosts = zabbix_get_hosts()
    hostid = None

    for h in hosts:
        if h["name"] == hostname:
            hostid = h["hostid"]
            break

    if hostid is None:
        raise ValueError(f"Host '{hostname}' not found in Zabbix")

    problems = zabbix_get_problems(hostids=[hostid], recent=True)

    for p in problems:
        if interface in p.get("name", ""):
            return p

    return None

# -------------------------
# ZABBIX
# -------------------------

ZABBIX_URL = "http://localhost/api_jsonrpc.php"
ZABBIX_TOKEN_FILE = "zabbix_token.txt"


def zabbix_load_token():
    with open(ZABBIX_TOKEN_FILE, "r") as f:
        return f.read().strip()


def zabbix_api(method, params, request_id=1):
    """Minimal JSON-RPC helper for Zabbix API calls."""
    token = zabbix_load_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }

    r = requests.post(ZABBIX_URL, json=payload, headers=headers)
    data = r.json()

    if "error" in data:
        raise RuntimeError(f"Zabbix API error ({method}): {data['error']}")

    return data.get("result", [])


def zabbix_get_hosts():
    return zabbix_api(
        "host.get",
        {
            "output": ["hostid", "host", "name", "status"]
        }
    )


def _extract_vlan_ids_from_ifname(ifname: str):
    """Extract VLAN IDs from common Linux subinterface naming conventions.

    Examples:
      eth1.100 -> 100
      ens192.4094 -> 4094
      vlan100 -> 100
      br100 -> 100  (useful in your router bridge naming)

    Returns a set of ints.
    """
    vlans = set()
    if not ifname:
        return vlans

    # ethX.<vid> / something.<vid>
    for m in re.finditer(r"\.(\d{1,4})(?:\b|$)", ifname):
        try:
            vlans.add(int(m.group(1)))
        except ValueError:
            pass

    # vlan<vid>
    for m in re.finditer(r"\bvlan(\d{1,4})\b", ifname, flags=re.IGNORECASE):
        try:
            vlans.add(int(m.group(1)))
        except ValueError:
            pass

    # br<vid> (your br100 naming)
    for m in re.finditer(r"\bbr(\d{1,4})\b", ifname, flags=re.IGNORECASE):
        try:
            vlans.add(int(m.group(1)))
        except ValueError:
            pass

    return vlans


def zabbix_get_discovered_interface_names(hostid: str):
    """Return interface names as seen in common net.if.* item keys.

    Zabbix interface LLD typically produces items with keys like:
      net.if.in[eth1.100,bytes]
      net.if.out[eth1.100,bytes]

    We pull item keys via item.get and parse the first parameter.
    """
    items = zabbix_api(
        "item.get",
        {
            "output": ["itemid", "name", "key_"],
            "hostids": hostid,
            # Reduce payload by only returning items whose key contains net.if.
            "search": {"key_": "net.if."},
            "searchByAny": True,
        }
    )

    ifnames = set()
    for it in items:
        key_ = it.get("key_", "")
        # Parse: net.if.in[<ifname>,bytes]
        m = re.search(r"net\.if\.[^\[]+\[([^,\]]+)", key_)
        if m:
            ifnames.add(m.group(1))

    return sorted(ifnames)


def zabbix_get_discovered_vlans_by_host(hostid: str):
    """Return sorted VLAN IDs inferred from discovered interface item keys."""
    ifnames = zabbix_get_discovered_interface_names(hostid)
    vlans = set()
    for ifn in ifnames:
        vlans |= _extract_vlan_ids_from_ifname(ifn)
    return sorted(vlans)


# -------------------------
# CLAB YAML intent parsing
# -------------------------

def parse_expected_vlans_from_clab(topo_file: str = CLAB_TOPO_FILE):
    """Parse expected VLAN IDs per node from a containerlab .clab.yml file.

    Strategy:
      1) Look for explicit 'ip link ... type vlan id <vid>' commands in node exec lists.
      2) Also infer VLANs from interface names that embed '.<vid>' in those exec commands.

    Returns: dict[str, list[int]] mapping node-name (bare, e.g. 'router1') -> sorted VLAN IDs.

    Note: Requires PyYAML (import yaml). If PyYAML is unavailable, raises RuntimeError.
    """
    if yaml is None:
        raise RuntimeError("PyYAML is not installed. Run: pip install pyyaml")

    p = Path(topo_file)
    if not p.exists():
        raise FileNotFoundError(f"Topology file not found: {topo_file}")

    data = yaml.safe_load(p.read_text())
    nodes = (((data or {}).get("topology") or {}).get("nodes") or {})

    expected = {}
    for node_name, node_def in nodes.items():
        vlans = set()

        exec_list = (node_def or {}).get("exec") or []
        # exec can be a list of strings
        if isinstance(exec_list, list):
            for cmd in exec_list:
                if not isinstance(cmd, str):
                    continue

                # Explicit: ... type vlan id 100
                for m in re.finditer(r"\btype\s+vlan\s+id\s+(\d{1,4})\b", cmd):
                    try:
                        vlans.add(int(m.group(1)))
                    except ValueError:
                        pass

                # Infer from 'name eth1.100' or similar
                # (e.g., ip link add link eth1 name eth1.100 ...)
                for m in re.finditer(r"\bname\s+([\w\-]+\.(\d{1,4}))\b", cmd):
                    try:
                        vlans.add(int(m.group(2)))
                    except ValueError:
                        pass

                # Also catch br100/vlan100 naming (your bridge naming)
                # vlans |= _extract_vlan_ids_from_ifname(cmd)

                # Explicit: ... type vlan id 100
                for m in re.finditer(r"\btype\s+vlan\s+id\s+(\d{1,4})\b", cmd):
                    vlans.add(int(m.group(1)))

                # Infer from interface names like eth1.100 (avoid matching IPs like 192.168.100.10)
                for token in re.findall(r"\b[A-Za-z][\w\-]*\.\d{1,4}\b", cmd):
                    vid = int(token.split(".")[-1])
                    vlans.add(vid)

        expected[node_name] = sorted(vlans)

    return expected

