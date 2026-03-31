#!/usr/bin/env python3
"""
log-pantry.py
Updates data/pantry-inventory.json by removing near-expiry items that have been consumed
and adding a snapshot of what was flagged this run.
Runs non-interactively — flags items expiring within 5 days for priority use.
"""

import json
import os
from datetime import date, timedelta

INVENTORY_PATH = "data/pantry-inventory.json"
EXPIRY_WARNING_DAYS = 5


def main():
    if not os.path.exists(INVENTORY_PATH):
        print(f"Creating empty pantry inventory at {INVENTORY_PATH}")
        inventory = {"last_updated": str(date.today()), "items": []}
        with open(INVENTORY_PATH, "w") as f:
            json.dump(inventory, f, indent=2)
        return

    with open(INVENTORY_PATH) as f:
        inventory = json.load(f)

    today = date.today()
    items = inventory.get("items", [])

    expiring_soon = []
    expired = []
    fresh = []

    for item in items:
        expiry_str = item.get("expiry_estimate")
        if not expiry_str:
            fresh.append(item)
            continue
        try:
            expiry = date.fromisoformat(expiry_str)
        except ValueError:
            fresh.append(item)
            continue

        days_left = (expiry - today).days
        if days_left < 0:
            expired.append(item)
        elif days_left <= EXPIRY_WARNING_DAYS:
            item["priority"] = "USE_SOON"
            item["days_until_expiry"] = days_left
            expiring_soon.append(item)
        else:
            fresh.append(item)

    # Report
    if expired:
        print(f"EXPIRED (removing {len(expired)} items):")
        for item in expired:
            print(f"  ✗ {item['name']} — expired {item['expiry_estimate']}")

    if expiring_soon:
        print(f"\nEXPIRING SOON (flag for priority use — {len(expiring_soon)} items):")
        for item in expiring_soon:
            print(f"  ⚠ {item['name']} — {item['days_until_expiry']} days left ({item['expiry_estimate']})")

    # Update inventory: remove expired, keep rest
    inventory["items"] = expiring_soon + fresh
    inventory["last_updated"] = str(today)
    inventory["expiring_soon_count"] = len(expiring_soon)

    with open(INVENTORY_PATH, "w") as f:
        json.dump(inventory, f, indent=2)

    total = len(inventory["items"])
    print(f"\nPantry updated: {total} items ({len(expired)} expired removed, {len(expiring_soon)} flagged for priority use)")


if __name__ == "__main__":
    main()
