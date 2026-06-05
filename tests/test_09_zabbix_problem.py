import time
from datetime import datetime
from helpers import zabbix_find_interface_problem


def test_zabbix_detects_interface_down():
    """
    After shutting down eth1.100 on router1,
    Zabbix should raise a PROBLEM.
    """
    hostname = "router1"
    interface = "eth1.100"

    # Zabbix is not instant — allow polling + trigger eval
    timeout = 60   # seconds
    interval = 5
    elapsed = 0
    problem = None

    while elapsed < timeout:
        problem = zabbix_find_interface_problem(hostname, interface)
        if problem:
            break
        print(f"  [{elapsed}s] No problem detected yet, retrying in {interval}s...")
        time.sleep(interval)
        elapsed += interval

    assert problem is not None, (
        f"Zabbix did not raise a problem for "
        f"{hostname} interface {interface} within {timeout}s"
    )

    # Format clock timestamp if present
    clock = problem.get("clock")
    detected_at = (
        datetime.fromtimestamp(int(clock)).strftime("%Y-%m-%d %H:%M:%S")
        if clock else "unknown"
    )

    severity_map = {
        "0": "Not classified",
        "1": "Information",
        "2": "Warning",
        "3": "Average",
        "4": "High",
        "5": "Disaster",
    }
    severity = severity_map.get(str(problem.get("severity", "")), "Unknown")

    col = 20
    print("\n")
    print(f"  {'Field':<{col}} Value")
    print(f"  {'-'*col} {'-'*40}")
    print(f"  {'Host':<{col}} {hostname}")
    print(f"  {'Interface':<{col}} {interface}")
    print(f"  {'Event ID':<{col}} {problem.get('eventid', 'N/A')}")
    print(f"  {'Problem name':<{col}} {problem.get('name', 'N/A')}")
    print(f"  {'Severity':<{col}} {severity}")
    print(f"  {'Detected at':<{col}} {detected_at}")
    print(f"  {'Detected after':<{col}} {elapsed}s")
    print()
