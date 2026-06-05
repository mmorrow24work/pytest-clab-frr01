"""Parallel 4-stream throughput: PC1 → PC2 via OSPF data plane.

Uses iperf3 -P 4 (four simultaneous streams).  The aggregate received
throughput should still be ≥ 1 Gbps — multi-stream exercises TCP
congestion control across the same path.
Also verifies that a reverse (PC2→PC1) measurement stays above threshold.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from helpers import iperf_run

MIN_MBPS = 1_000


def test_iperf_parallel_streams_pc1_to_pc2():
    """4 parallel streams PC1→PC2 yield ≥ 1 Gbps aggregate."""
    mbps = iperf_run(
        server_container="clab-frr01-PC2",
        client_container="clab-frr01-PC1",
        server_ip="192.168.12.2",
        duration=5,
        parallel=4,
    )
    print(f"\n  PC1→PC2 parallel-4 throughput: {mbps:.0f} Mbps")
    assert mbps >= MIN_MBPS, (
        f"Parallel throughput {mbps:.0f} Mbps below minimum {MIN_MBPS} Mbps"
    )


def test_iperf_reverse_pc2_to_pc1():
    """Reverse direction (PC2→PC1) yields ≥ 1 Gbps."""
    mbps = iperf_run(
        server_container="clab-frr01-PC2",
        client_container="clab-frr01-PC1",
        server_ip="192.168.12.2",
        duration=5,
        reverse=True,
    )
    print(f"\n  PC2→PC1 reverse throughput: {mbps:.0f} Mbps")
    assert mbps >= MIN_MBPS, (
        f"Reverse throughput {mbps:.0f} Mbps below minimum {MIN_MBPS} Mbps"
    )
