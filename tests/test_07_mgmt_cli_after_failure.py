from helpers import ALL_NODES, interface_is_up


def test_management_interfaces_still_up():
    for node in ALL_NODES:
        assert interface_is_up(node, "eth0")
