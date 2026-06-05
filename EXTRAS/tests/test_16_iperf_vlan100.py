"""VLAN 100 bridge throughput — PC1.100 → PC2.100 and PC1.100 → router1 br100.

VLAN 100 spans all three routers via eth1.100/eth2.100/eth3.100 trunks and br100.
PCs connect via eth1.100 (192.168.100.1-3); router bridge IPs are .10/.20/.30.

Tests:
  1. PC1 (192.168.100.1) → PC2 (192.168.100.2)  — L2 path across two routers
  2. PC1 (192.168.100.1) → router1 br100 (192.168.100.10) — direct L2 path
Asserts: ≥ 1 000 Mbps.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from helpers import iperf_run

MIN_MBPS = 1_000

VLAN100_PAIRS = [
    ("clab-frr01-PC1", "clab-frr01-PC2",     "192.168.100.2",  "PC1→PC2 via VLAN100"),
    ("clab-frr01-PC1", "clab-frr01-router1",  "192.168.100.10", "PC1→router1 br100"),
]


@pytest.mark.parametrize("client,server,server_ip,label", VLAN100_PAIRS,
                         ids=[x[3] for x in VLAN100_PAIRS])
def test_iperf_vlan100(client, server, server_ip, label):
    """VLAN 100 path achieves ≥ 1 Gbps."""
    mbps = iperf_run(
        server_container=server,
        client_container=client,
        server_ip=server_ip,
        duration=5,
    )
    print(f"\n  {label} throughput: {mbps:.0f} Mbps")
    assert mbps >= MIN_MBPS, (
        f"{label} throughput {mbps:.0f} Mbps below minimum {MIN_MBPS} Mbps"
    )
