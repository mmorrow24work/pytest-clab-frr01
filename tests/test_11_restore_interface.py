import time
import subprocess
from helpers import interface_is_up


def _ip_link_set_up(container: str, iface: str):
    # mirror your existing helper style (docker exec + sh -c)
    cmd = f"docker exec {container} sh -c 'ip link set {iface} up'"
    subprocess.run(cmd, shell=True, check=True)


def test_restore_vlan():
    """
    Restore the VLAN subinterface eth1.100 on router1 and verify it comes UP.
    """
    container = "clab-frr01-router1"
    iface = "eth1.100"

    _ip_link_set_up(container, iface)

    # Give Linux/Zabbix-agent a moment; poll until link is UP
    timeout = 30
    interval = 2
    end_time = time.time() + timeout

    while time.time() < end_time:
        if interface_is_up(container, iface):
            break
        time.sleep(interval)

    assert interface_is_up(container, iface), f"{container} {iface} did not return to UP within {timeout}s"
