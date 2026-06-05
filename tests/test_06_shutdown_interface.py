from helpers import shutdown_interface, interface_is_up


def test_shutdown_vlan():
    node = "clab-frr01-router1"
    iface = "eth1.100"

    # Show before state
    before_up = interface_is_up(node, iface)
    before_status = "✓ up" if before_up else "✗ down"

    print("\n")
    col = 35
    print(f"  {'Attribute':<20} {'Value'}")
    print(f"  {'-'*20} {'-'*40}")
    print(f"  {'Node':<{col}} {node}")
    print(f"  {'Interface':<{col}} {iface}")
    print(f"  {'Before shutdown':<20} {before_status}")

    shutdown_interface(node, iface)

    # Show after state
    after_up = interface_is_up(node, iface)
    after_status = "✓ up" if after_up else "✗ down"

    print(f"  {'After shutdown':<20} {after_status}")
    print()

    assert not after_up, (
        f"Expected {node}:{iface} to be down after shutdown_interface, "
        f"but it is {after_status}. "
        f"Before: {before_status}"
    )
