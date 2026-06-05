"""Session-scoped fixtures for the EXTRAS test suite.

Ensures each router host in Zabbix has:
  - An SNMP (type 2) interface so the server can match incoming traps to hosts
  - A snmptrap.fallback item so trap data is stored in Zabbix history
"""

import pytest
import requests

ZABBIX_URL = "http://localhost/api_jsonrpc.php"
TOKEN_CANDIDATES = [
    "/home/mickm/git/containerlab/lab-examples/frr01/zabbix_token.txt",
    "/home/mickm/git/pytest-clab-frr01/zabbix_token.txt",
]

ROUTER_HOSTS = {
    "router1": "172.18.0.41",
    "router2": "172.18.0.42",
    "router3": "172.18.0.43",
}


def _zbx(token, method, params):
    r = requests.post(
        ZABBIX_URL,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
        timeout=10,
    )
    r.raise_for_status()
    d = r.json()
    if "error" in d:
        raise RuntimeError(f"Zabbix {method} error: {d['error']['data']}")
    return d["result"]


@pytest.fixture(scope="session")
def zbx_token():
    for path in TOKEN_CANDIDATES:
        try:
            return open(path).read().strip()
        except FileNotFoundError:
            continue
    pytest.skip("zabbix_token.txt not found")


@pytest.fixture(scope="session")
def zbx_snmptrap_items(zbx_token):
    """Ensure router hosts have SNMP interface + snmptrap.fallback item.

    Returns dict: {host_name: item_id}
    """
    token = zbx_token

    hosts = _zbx(token, "host.get", {
        "output": ["hostid", "name"],
        "selectInterfaces": ["interfaceid", "type", "ip"],
        "filter": {"name": list(ROUTER_HOSTS.keys())},
    })
    host_map = {h["name"]: h for h in hosts}

    item_ids = {}
    for host_name, mgmt_ip in ROUTER_HOSTS.items():
        host = host_map.get(host_name)
        if not host:
            continue
        hostid = host["hostid"]
        ifaces = host["interfaces"]

        # Add SNMP interface if not already present
        snmp_ifaces = [i for i in ifaces if i["type"] == "2"]
        if snmp_ifaces:
            snmp_iface_id = snmp_ifaces[0]["interfaceid"]
        else:
            res = _zbx(token, "hostinterface.create", {
                "hostid": hostid,
                "main": "1",
                "type": "2",
                "useip": "1",
                "ip": mgmt_ip,
                "dns": "",
                "port": "161",
                "details": {
                    "version": "2",
                    "community": "public",
                    "bulk": "1",
                    "securityname": "",
                    "securitylevel": "0",
                    "authpassphrase": "",
                    "privpassphrase": "",
                    "authprotocol": "0",
                    "privprotocol": "0",
                    "contextname": "",
                },
            })
            snmp_iface_id = res["interfaceids"][0]

        # Create snmptrap.fallback item if not present
        existing = _zbx(token, "item.get", {
            "output": ["itemid"],
            "hostids": [hostid],
            "search": {"key_": "snmptrap.fallback"},
        })
        if existing:
            item_ids[host_name] = existing[0]["itemid"]
        else:
            res = _zbx(token, "item.create", {
                "hostid": hostid,
                "name": "SNMP traps (fallback)",
                "key_": "snmptrap.fallback",
                "type": "17",       # SNMP trap
                "value_type": "2",  # Log
                "delay": "0",
                "logtimefmt": "hh:mm:ssdd/MM/yyyy",
                "interfaceid": snmp_iface_id,
            })
            item_ids[host_name] = res["itemids"][0]

    return item_ids
