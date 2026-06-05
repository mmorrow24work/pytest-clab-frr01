"""SNMP trap test: router2 sends a linkDown trap; OID is verified in log.

Uses IF-MIB::linkDown with an ifIndex varbind. Checks that the correct OID
string appears alongside the source IP in snmptraps.log.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from helpers import snmptraps_log_size, snmp_trap_send, snmptrap_wait_for, NODE_MGMT_IP

SOURCE_CONTAINER = "clab-frr01-router2"
SOURCE_IP = NODE_MGMT_IP[SOURCE_CONTAINER]


def test_snmp_linkdown_trap_oid_present():
    """linkDown trap from router2 appears with correct OID in snmptraps.log."""
    before = snmptraps_log_size()

    snmp_trap_send(
        SOURCE_CONTAINER,
        oid="IF-MIB::linkDown",
        extra_varbinds=[
            "IF-MIB::ifIndex.1", "i", "1",
            "IF-MIB::ifAdminStatus.1", "i", "1",
            "IF-MIB::ifOperStatus.1", "i", "2",
        ],
    )

    found, snippet = snmptrap_wait_for(SOURCE_IP, before,
                                       oid_substring="linkDown", timeout=15)
    print(f"\n  Trap log snippet:\n{snippet}")
    assert found, (
        f"No linkDown trap from {SOURCE_IP} with correct OID found within 15 s"
    )
