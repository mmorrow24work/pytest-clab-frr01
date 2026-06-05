from helpers import ROUTERS, PCS, interface_is_up


def test_router_interfaces():
    interfaces = ["eth1", "eth2", "eth3", "eth1.100", "eth2.100", "eth3.100", "br100"]

    print("\n")
    col = 20
    print(f"  {'Router':<{col}} {'Interface':<15} {'Status'}")
    print(f"  {'-'*col} {'-'*15} {'------'}")

    failures = []

    for router in sorted(ROUTERS):
        for iface in interfaces:
            up = interface_is_up(router, iface)
            status = "✓" if up else "✗"
            print(f"  {router:<{col}} {iface:<15} {status}")
            if not up:
                failures.append(f"{router}:{iface}")

    print()

    assert len(failures) == 0, (
        f"One or more router interfaces are down: {', '.join(failures)}. "
        f"ROUTERS: {ROUTERS}, interfaces: {interfaces}"
    )


def test_pc_interfaces():
    interfaces = ["eth1", "eth1.100"]

    print("\n")
    col = 20
    print(f"  {'PC':<{col}} {'Interface':<15} {'Status'}")
    print(f"  {'-'*col} {'-'*15} {'------'}")

    failures = []

    for pc in sorted(PCS):
        for iface in interfaces:
            up = interface_is_up(pc, iface)
            status = "✓" if up else "✗"
            print(f"  {pc:<{col}} {iface:<15} {status}")
            if not up:
                failures.append(f"{pc}:{iface}")

    print()

    assert len(failures) == 0, (
        f"One or more PC interfaces are down: {', '.join(failures)}. "
        f"PCS: {PCS}, interfaces: {interfaces}"
    )
