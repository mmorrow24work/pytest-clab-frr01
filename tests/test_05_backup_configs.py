from helpers import ROUTERS, backup_frr_config
from pathlib import Path


def test_backup_configs():
    print("\n")
    col = 25
    print(f"  {'Router':<{col}} {'File':<60} {'Exists'}")
    print(f"  {'-'*col} {'-'*60} {'------'}")

    failures = []

    for router in sorted(ROUTERS):
        filename = backup_frr_config(router)
        exists = Path(filename).exists()
        status = "✓" if exists else "✗"
        # Truncate long paths for readability if needed
        file_display = filename if len(filename) <= 60 else "..." + filename[-57:]
        print(f"  {router:<{col}} {file_display:<60} {status}")
        if not exists:
            failures.append(f"{router}:{filename}")

    print()

    assert len(failures) == 0, (
        f"One or more router config backups are missing: {', '.join(failures)}. "
        f"ROUTERS: {ROUTERS}"
    )
