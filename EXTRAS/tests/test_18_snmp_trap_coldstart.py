"""SNMP trap test: router1 sends a coldStart trap; Zabbix snmptrapd receives it.

Validates the end-to-end trap delivery path:
  router1 (snmptrap CLI) → 172.18.0.5:1162 (snmptrapd) → snmptraps.log
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from helpers import snmptraps_log_size, snmp_trap_send, snmptrap_wait_for, NODE_MGMT_IP

SOURCE_CONTAINER = "clab-frr01-router1"
SOURCE_IP = NODE_MGMT_IP[SOURCE_CONTAINER]


def test_snmp_coldstart_trap_received():
    """coldStart trap from router1 appears in Zabbix snmptraps.log within 15 s."""
    before = snmptraps_log_size()

    snmp_trap_send(SOURCE_CONTAINER, oid="SNMPv2-MIB::coldStart.0")

    found, snippet = snmptrap_wait_for(SOURCE_IP, before,
                                       oid_substring="coldStart", timeout=15)
    print(f"\n  Trap log snippet:\n{snippet}")
    assert found, (
        f"No coldStart trap from {SOURCE_IP} found in snmptraps.log within 15 s"
    )
