from helpers import (
    zabbix_get_hosts,
    zabbix_get_discovered_vlans_by_host,
    parse_expected_vlans_from_clab,
    CLAB_TOPO_FILE,
)


def test_zabbix_vlans_match_clab():
    """
    Compare VLANs (intent from clab YAML) with VLANs discovered in Zabbix.

    Prints a per-host comparison table when run with: pytest -s
    """
    # Expected VLANs per node from the lab topology file
    expected_by_node = parse_expected_vlans_from_clab(CLAB_TOPO_FILE)

    # Zabbix hosts visible via API
    hosts = zabbix_get_hosts()
    hostid_by_name = {h["name"]: h["hostid"] for h in hosts}

    col1, col2, col3 = 18, 22, 22
    print("\n")
    print(f"  {'Host':<{col1}} {'Clab VLANs':<{col2}} {'Zabbix VLANs':<{col3}} Match")
    print(f"  {'-'*col1} {'-'*col2} {'-'*col3} -----")

    mismatches = []

    # Compare for all nodes that exist in the YAML
    for node_name in sorted(expected_by_node.keys()):
        expected_vlans = expected_by_node.get(node_name, [])

        hostid = hostid_by_name.get(node_name)
        if not hostid:
            # Zabbix missing host entirely
            print(f"  {node_name:<{col1}} {str(expected_vlans):<{col2}} {'(missing)':<{col3}} ✗")
            mismatches.append((node_name, expected_vlans, None))
            continue

        discovered_vlans = zabbix_get_discovered_vlans_by_host(hostid)

        match = sorted(expected_vlans) == sorted(discovered_vlans)
        symbol = "✓" if match else "✗"

        print(
            f"  {node_name:<{col1}} "
            f"{str(expected_vlans):<{col2}} "
            f"{str(discovered_vlans):<{col3}} "
            f"{symbol}"
        )

        if not match:
            mismatches.append((node_name, expected_vlans, discovered_vlans))

    print()

    assert not mismatches, "VLAN mismatch(es): " + ", ".join(
        f"{n} clab={e} zbx={z}" for (n, e, z) in mismatches
    )
