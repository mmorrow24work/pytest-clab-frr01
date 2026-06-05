from helpers import ALL_NODES, interface_is_up


def test_management_interfaces():
    # Collect results once
    results = [(node, interface_is_up(node, "eth0")) for node in ALL_NODES]

    # Print a comparison table (visible with pytest -s)
    print("\n")
    col = 30
    print(f"  {'Node':<{col}} {'Interface':<10} {'Status'}")
    print(f"  {'-'*col} {'-'*10} {'------'}")

    all_failed = []

    for node, up in results:
        status = "✓" if up else "✗"
        print(f"  {node:<{col}} {'eth0':<10} {status}")
        if not up:
            all_failed.append(node)

    print()

    assert all(up for _, up in results), (
        f"One or more management interfaces are down: {', '.join(all_failed)}. "
        f"Clab nodes: {ALL_NODES}"
    )
