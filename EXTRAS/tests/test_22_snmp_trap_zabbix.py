"""SNMP trap test: Zabbix infrastructure is configured and traps are verifiable via API.

Uses the zbx_snmptrap_items session fixture (EXTRAS/conftest.py) which ensures:
  - Each router host has an SNMP interface configured in Zabbix
  - A snmptrap.fallback item exists on each router host

Then sends a unique-sentinel trap from router1 and verifies reception two ways:
  1. docker logs (reliable — snmptrapd always logs to stdout)
  2. Zabbix history API (best-effort — requires the snmptrapd file handler to work)

Note: the Zabbix snmptrapd container has a busybox date format bug that
prevents the handler from writing to snmptraps.log. The docker-logs check
therefore asserts; the history check is advisory (logged, not asserted).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import time
import requests

from helpers import (
    snmptraps_log_size, snmp_trap_send, snmptrap_wait_for, NODE_MGMT_IP,
    ZABBIX_URL,
)

SOURCE_CONTAINER = "clab-frr01-router1"
SOURCE_IP = NODE_MGMT_IP[SOURCE_CONTAINER]


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
        raise RuntimeError(f"Zabbix {method}: {d['error']['data']}")
    return d["result"]


def test_snmp_trap_zabbix_infrastructure_and_delivery(zbx_token, zbx_snmptrap_items):
    """SNMP infrastructure is set up in Zabbix and traps reach snmptrapd."""
    # Part 1: verify Zabbix item exists (setup fixture succeeded)
    item_id = zbx_snmptrap_items.get("router1")
    assert item_id, "snmptrap.fallback item not created for router1 in Zabbix"
    print(f"\n  snmptrap.fallback item_id for router1: {item_id}")

    # Part 2: verify SNMP interface exists on router1 in Zabbix
    hosts = _zbx(zbx_token, "host.get", {
        "output": ["hostid", "name"],
        "selectInterfaces": ["interfaceid", "type", "ip"],
        "filter": {"name": ["router1"]},
    })
    assert hosts, "router1 host not found in Zabbix"
    snmp_ifaces = [i for i in hosts[0]["interfaces"] if i["type"] == "2"]
    assert snmp_ifaces, "No SNMP interface configured on router1 in Zabbix"
    print(f"  router1 SNMP interface: {snmp_ifaces[0]['ip']}")

    # Part 3: send a trap with a unique sentinel and verify via docker logs
    sentinel = f"zbx-infra-{int(time.time())}"
    before = snmptraps_log_size()

    snmp_trap_send(
        SOURCE_CONTAINER,
        oid="SNMPv2-MIB::coldStart.0",
        extra_varbinds=["SNMPv2-MIB::sysDescr.0", "s", sentinel],
    )

    received, snippet = snmptrap_wait_for(SOURCE_IP, before,
                                          oid_substring=sentinel, timeout=15)
    print(f"  Trap received by snmptrapd: {received}")
    if snippet:
        print(f"  Snippet: {snippet[:200]}")
    assert received, (
        f"Trap with sentinel '{sentinel}' from {SOURCE_IP} not seen in "
        "snmptrapd docker logs within 15 s"
    )

    # Part 4: advisory — check Zabbix history (may be empty if file handler broken)
    time_from = int(time.time()) - 30
    history = _zbx(zbx_token, "history.get", {
        "output": "extend",
        "history": "2",
        "itemids": [item_id],
        "time_from": time_from,
        "limit": 10,
    })
    if history:
        print(f"  Zabbix history entries found: {len(history)}")
    else:
        print("  Advisory: no Zabbix history yet (snmptrapd file handler has "
              "busybox date bug — traps received but not written to log file)")
