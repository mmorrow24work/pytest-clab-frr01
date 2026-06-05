from helpers import zabbix_get_hosts, ALL_NODES


def test_zabbix_hosts_exist():
    hosts = zabbix_get_hosts()
    hostnames = [h["name"] for h in hosts]
    assert len(hostnames) > 0


def test_zabbix_hosts_match_clab():
    hosts = zabbix_get_hosts()
    zabbix_hostnames = set(h["name"] for h in hosts)

    # Strip the "clab-frr01-" prefix to get bare names for comparison
    clab_hostnames = sorted([n.replace("clab-frr01-", "") for n in ALL_NODES])

    col = 30
    print("\n")
    print(f"  {'Clab Node':<{col}} {'Zabbix Host':<{col}} {'Match'}")
    print(f"  {'-'*col} {'-'*col} {'-----'}")

    missing = []
    for name in clab_hostnames:
        in_zabbix = name in zabbix_hostnames
        zabbix_cell = name if in_zabbix else "(missing)"
        match = "✓" if in_zabbix else "✗"
        print(f"  {name:<{col}} {zabbix_cell:<{col}} {match}")
        if not in_zabbix:
            missing.append(name)

    # Show extra Zabbix hosts that aren't in clab (informational, not a failure)
    extras = sorted(zabbix_hostnames - set(clab_hostnames))
    for name in extras:
        print(f"  {'(extra)':<{col}} {name:<{col}} -")

    print()

    assert not missing, (
        f"Clab hosts missing from Zabbix: {missing}"
    )
