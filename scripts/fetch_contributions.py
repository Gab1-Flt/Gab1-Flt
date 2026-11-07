#!/usr/bin/env python3
"""
Fetch public GitHub contribution calendar data for a user without requiring an API token.
Saves structured 53-week contribution data to data/contributions.json.
"""

import datetime as dt
import json
import os
import re
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_PROFILE_USER", "Gab1-Flt")
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_github_contributions(username: str) -> dict:
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ASCIIProfileKit/1.0)",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Extract total contributions header if available
    # e.g., "142 contributions in the last year"
    total_match = re.search(
        r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", html, re.IGNORECASE
    )
    total_contributions = (
        int(total_match.group(1).replace(",", "")) if total_match else 0
    )

    # Extract all cells with data-date and data-level
    # GitHub renders <td ... data-date="2026-05-12" ... data-level="2" ...>
    cell_pattern = re.compile(
        r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"[^>]*>',
        re.IGNORECASE,
    )
    alt_pattern = re.compile(
        r'<td[^>]*data-level="(\d)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*>',
        re.IGNORECASE,
    )

    days_map = {}
    for m in cell_pattern.finditer(html):
        d_str, level_str = m.group(1), m.group(2)
        days_map[d_str] = int(level_str)

    if not days_map:
        for m in alt_pattern.finditer(html):
            level_str, d_str = m.group(1), m.group(2)
            days_map[d_str] = int(level_str)

    # Also parse tooltip counts if present:
    # <tool-tip ... for="contribution-day-component-...">3 contributions on May 12th.</tool-tip>
    sorted_dates = sorted(days_map.keys())
    days_list = [
        {"date": d, "level": days_map[d]}
        for d in sorted_dates
    ]

    if not total_contributions and days_list:
        # Estimate from levels if total text wasn't matched
        level_weights = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}
        total_contributions = sum(level_weights.get(item["level"], 0) for item in days_list)

    return {
        "user": username,
        "updated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_contributions": total_contributions,
        "days": days_list,
    }


def generate_fallback_calendar(username: str) -> dict:
    """Generate a clean 53-week calendar grid ending today when offline."""
    today = dt.date.today()
    # Start 52 weeks ago on Sunday
    days_since_sunday = (today.weekday() + 1) % 7
    end_sunday = today - dt.timedelta(days=days_since_sunday)
    start_date = end_sunday - dt.timedelta(weeks=52)

    days_list = []
    cur = start_date
    while cur <= today:
        days_list.append({"date": cur.isoformat(), "level": 0})
        cur += dt.timedelta(days=1)

    return {
        "user": username,
        "updated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_contributions": 0,
        "days": days_list,
    }


def main():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = fetch_github_contributions(USER)
        if not data.get("days"):
            raise ValueError("No contribution cells found in response")
        print(
            f"Fetched {len(data['days'])} days ({data['total_contributions']} total contributions) for {USER}"
        )
    except Exception as exc:
        print(f"Warning: live fetch failed ({exc}).")
        if DATA_PATH.exists():
            print("Keeping existing data/contributions.json")
            return
        print("Creating initial calendar structure in data/contributions.json")
        data = generate_fallback_calendar(USER)

    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved {DATA_PATH}")


if __name__ == "__main__":
    main()

