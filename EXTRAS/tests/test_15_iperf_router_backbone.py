"""Router backbone link throughput — all three inter-router links.

Links:
  r1↔r2: 192.168.1.0/24  (r1=.1, r2=.2)
  r1↔r3: 192.168.2.0/24  (r1=.1, r3=.2)
  r2↔r3: 192.168.3.0/24  (r2=.1, r3=.2)

Each test runs iperf3 client on the near router, server on the far router,
using the direct peer IP (no routing through third node).
Asserts: ≥ 1 000 Mbps per link.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from helpers import iperf_run

MIN_MBPS = 1_000

BACKBONE_LINKS = [
    ("clab-frr01-router1", "clab-frr01-router2", "192.168.1.2", "r1→r2"),
    ("clab-frr01-router1", "clab-frr01-router3", "192.168.2.2", "r1→r3"),
    ("clab-frr01-router2", "clab-frr01-router3", "192.168.3.2", "r2→r3"),
]


@pytest.mark.parametrize("client,server,server_ip,label", BACKBONE_LINKS,
                         ids=[x[3] for x in BACKBONE_LINKS])
def test_iperf_backbone_link(client, server, server_ip, label):
    """Each backbone link achieves ≥ 1 Gbps."""
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
