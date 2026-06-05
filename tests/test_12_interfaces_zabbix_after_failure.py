import time
from helpers import (
    zabbix_get_hosts,
    zabbix_get_problems,
)


def test_zabbix_problem_cleared_after_restore():
    """
    After restoring eth1.100 on router1, the Zabbix PROBLEM
    'Linux: Interface eth1.100: Link down' should be cleared.
    """

    hostname = "router1"
    interface = "eth1.100"

    # Resolve host ID
    hosts = zabbix_get_hosts()
    hostid = None
    for h in hosts:
        if h["name"] == hostname:
            hostid = h["hostid"]
            break

    assert hostid is not None, f"Host '{hostname}' not found in Zabbix"

    timeout = 120   # allow Zabbix recovery & trigger evaluation
    interval = 5
    end_time = time.time() + timeout

    while time.time() < end_time:
        problems = zabbix_get_problems(hostids=[hostid], recent=False)

        # Look for unresolved problems mentioning the interface
        interface_problems = [
            p for p in problems
            if interface in p.get("name", "")
        ]

        if not interface_problems:
            # ✅ Problem has cleared
            return

        time.sleep(interval)

    # If we get here, the problem never cleared
    raise AssertionError(
        f"Zabbix problem for {hostname} {interface} did not clear within {timeout}s"
    )
