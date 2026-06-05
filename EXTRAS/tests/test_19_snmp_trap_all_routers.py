"""SNMP trap test: all three routers send traps; all appear in snmptraps.log.

Sends a warmStart trap from each router simultaneously and verifies that
all three source IPs are logged within 20 s. Tests that snmptrapd can
handle concurrent traps from multiple sources.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import threading
from helpers import (
    snmptraps_log_size, snmp_trap_send, snmptrap_wait_for,
    ROUTERS, NODE_MGMT_IP,
)


def test_snmp_trap_all_routers_received():
    """warmStart traps from all 3 routers all appear in snmptraps.log."""
    before = snmptraps_log_size()

    # Send traps concurrently from all three routers
    threads = [
        threading.Thread(
            target=snmp_trap_send,
            args=(r,),
            kwargs={"oid": "SNMPv2-MIB::warmStart.0"},
            daemon=True,
        )
        for r in ROUTERS
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    # Verify each router's trap landed in the log
    missing = []
    for router in ROUTERS:
        src_ip = NODE_MGMT_IP[router]
        found, snippet = snmptrap_wait_for(src_ip, before,
                                           oid_substring="warmStart", timeout=20)
        if found:
            print(f"\n  {router} ({src_ip}) trap received")
        else:
            missing.append(f"{router} ({src_ip})")

    assert not missing, (
        f"Trap(s) not received from: {', '.join(missing)}"
    )
