"""PC2 → PC3 data-plane throughput via OSPF routing.

Path: PC2 eth1 (192.168.12.2) → router2 eth3 → OSPF → router3 eth3 → PC3 eth1 (192.168.13.2)
Asserts: ≥ 1 000 Mbps.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from helpers import iperf_run

MIN_MBPS = 1_000


def test_iperf_pc2_to_pc3_throughput():
    """PC2 achieves ≥ 1 Gbps to PC3 across the OSPF data plane."""
    mbps = iperf_run(
        server_container="clab-frr01-PC3",
        client_container="clab-frr01-PC2",
        server_ip="192.168.13.2",
        duration=5,
    )
    print(f"\n  PC2→PC3 throughput: {mbps:.0f} Mbps")
    assert mbps >= MIN_MBPS, (
        f"Throughput {mbps:.0f} Mbps below minimum {MIN_MBPS} Mbps"
    )
