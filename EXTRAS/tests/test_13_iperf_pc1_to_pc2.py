"""PC1 → PC2 data-plane throughput via OSPF routing.

Path: PC1 eth1 (192.168.11.2) → router1 eth3 → OSPF → router2 eth3 → PC2 eth1 (192.168.12.2)
Asserts: ≥ 1 000 Mbps (1 Gbps) — Docker veth links are virtual, so this is easily achievable.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from helpers import iperf_run

MIN_MBPS = 1_000


def test_iperf_pc1_to_pc2_throughput():
    """PC1 achieves ≥ 1 Gbps to PC2 across the OSPF data plane."""
    mbps = iperf_run(
        server_container="clab-frr01-PC2",
        client_container="clab-frr01-PC1",
        server_ip="192.168.12.2",
        duration=5,
    )
    print(f"\n  PC1→PC2 throughput: {mbps:.0f} Mbps")
    assert mbps >= MIN_MBPS, (
        f"Throughput {mbps:.0f} Mbps below minimum {MIN_MBPS} Mbps"
    )
