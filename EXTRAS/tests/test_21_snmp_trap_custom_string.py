"""SNMP trap test: custom varbind string is preserved in snmptraps.log.

Sends a trap from router3 with a sysDescr.0 varbind containing a unique
sentinel string. Verifies that the sentinel appears verbatim in the log,
confirming varbind payload is not truncated or dropped.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import time
from helpers import snmptraps_log_size, snmp_trap_send, snmptrap_wait_for, NODE_MGMT_IP

SOURCE_CONTAINER = "clab-frr01-router3"
SOURCE_IP = NODE_MGMT_IP[SOURCE_CONTAINER]
SENTINEL = f"pytest-frr01-sentinel-{int(time.time())}"


def test_snmp_trap_custom_varbind_preserved():
    """Unique sentinel string in sysDescr.0 varbind appears in snmptraps.log."""
    before = snmptraps_log_size()

    snmp_trap_send(
        SOURCE_CONTAINER,
        oid="SNMPv2-MIB::coldStart.0",
        extra_varbinds=[
            "SNMPv2-MIB::sysDescr.0", "s", SENTINEL,
        ],
    )

    found, snippet = snmptrap_wait_for(SOURCE_IP, before,
                                       oid_substring=SENTINEL, timeout=15)
    print(f"\n  Sentinel: {SENTINEL}")
    print(f"  Trap log snippet:\n{snippet}")
    assert found, (
        f"Sentinel '{SENTINEL}' not found in snmptraps.log within 15 s"
    )
