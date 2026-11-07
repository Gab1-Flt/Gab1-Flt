#!/usr/bin/env python3
"""
Render an animated terminal-styled GitHub contribution heatmap SVG (contrib-heatmap.svg)
from data/contributions.json.
"""

import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "contributions.json"
OUTPUT_PATH = ROOT / "contrib-heatmap.svg"

LEVEL_COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}


def compute_streaks(days: list[dict]) -> tuple[int, int]:
    """Compute (longest_streak, current_streak) from sorted day dicts."""
    longest = 0
    current = 0
    running = 0
    for d in days:
        if d.get("level", 0) > 0:
            running += 1
            if running > longest:
                longest = running
        else:
            running = 0

    # Current streak: count backwards from today (or yesterday if today is 0)
    for idx in range(len(days) - 1, -1, -1):
        lvl = days[idx].get("level", 0)
        if idx == len(days) - 1 and lvl == 0:
            continue
        if lvl > 0:
            current += 1
        else:
            break

    return longest, current


def render_heatmap_svg(data: dict) -> str:
    user = data.get("user", "Gab1-Flt")
    total = data.get("total_contributions", 0)
    days = data.get("days", [])
    updated_raw = data.get("updated_at", "")
    updated_date = updated_raw[:10] if updated_raw else dt.date.today().isoformat()

    # Organize days into weekly columns (Sunday = row 0 .. Saturday = row 6)
    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = [None] * 7

    for item in days:
        d_obj = dt.date.fromisoformat(item["date"])
        dow = (d_obj.weekday() + 1) % 7  # Sunday=0 .. Saturday=6
        if dow == 0 and any(x is not None for x in current_week):
            weeks.append(current_week)
            current_week = [None] * 7
        current_week[dow] = {
            "date": item["date"],
            "level": int(item.get("level", 0)),
            "month": d_obj.strftime("%b"),
            "day": d_obj.day,
        }
    if any(x is not None for x in current_week):
        weeks.append(current_week)

    # Keep last 53 weeks max
    if len(weeks) > 53:
        weeks = weeks[-53:]

    longest_streak, current_streak = compute_streaks(days)

    width = 880
    height = 248
    cell_size = 11
    cell_gap = 3
    step = cell_size + cell_gap
    grid_x0 = 56
    grid_y0 = 102

    # Month labels along top of columns
    month_labels = []
    last_month = None
    for w_idx, week in enumerate(weeks):
        first_valid = next((c for c in week if c is not None), None)
        if first_valid:
            m_name = first_valid["month"]
            if m_name != last_month and first_valid["day"] <= 14:
                x = grid_x0 + w_idx * step
                month_labels.append(
                    f'<text x="{x}" y="{grid_y0 - 8}" class="mono" font-size="10" fill="#8b949e">{m_name}</text>'
                )
                last_month = m_name

    # Day of week labels (Mon, Wed, Fri)
    dow_labels = [
        f'<text x="24" y="{grid_y0 + 1 * step + 9}" class="mono" font-size="10" fill="#8b949e">Mon</text>',
        f'<text x="24" y="{grid_y0 + 3 * step + 9}" class="mono" font-size="10" fill="#8b949e">Wed</text>',
        f'<text x="24" y="{grid_y0 + 5 * step + 9}" class="mono" font-size="10" fill="#8b949e">Fri</text>',
    ]

    # Contribution cells grouped by column for smooth wave animation
    col_groups = []
    css_cols = []
    for w_idx, week in enumerate(weeks):
        delay = 0.15 + w_idx * 0.018
        css_cols.append(
            f".c{w_idx} {{ opacity: 0; animation: fadeCell 0.35s ease forwards {delay:.3f}s; }}"
        )
        rects = []
        x = grid_x0 + w_idx * step
        for dow, cell in enumerate(week):
            if cell is None:
                continue
            y = grid_y0 + dow * step
            lvl = cell["level"]
            fill = LEVEL_COLORS.get(lvl, LEVEL_COLORS[0])
            stroke = "#21262d" if lvl == 0 else "none"
            sw = ' stroke="#21262d" stroke-width="0.8"' if stroke != "none" else ""
            rects.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{fill}"{sw}>'
                f"<title>{cell['date']} (level {lvl})</title></rect>"
            )
        col_groups.append(f'  <g class="c{w_idx}">' + "".join(rects) + "</g>")

    # Legend on bottom right
    legend_y = grid_y0 + 7 * step + 18
    legend_x = width - 175
    legend_items = [
        f'<text x="{legend_x - 32}" y="{legend_y + 9}" class="mono" font-size="10" fill="#8b949e">Less</text>'
    ]
    for lvl in range(5):
        lx = legend_x + lvl * (cell_size + 3)
        fill = LEVEL_COLORS[lvl]
        sw = ' stroke="#21262d" stroke-width="0.8"' if lvl == 0 else ""
        legend_items.append(
            f'<rect x="{lx}" y="{legend_y}" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{fill}"{sw}/>'
        )
    legend_items.append(
        f'<text x="{legend_x + 5 * (cell_size + 3) + 4}" y="{legend_y + 9}" class="mono" font-size="10" fill="#8b949e">More</text>'
    )

    css_joined = "\n      ".join(css_cols)
    months_joined = "\n  ".join(month_labels)
    dows_joined = "\n  ".join(dow_labels)
    cols_joined = "\n".join(col_groups)
    legend_joined = "\n  ".join(legend_items)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <style>
      .mono {{
        font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      }}
      @keyframes fadeCell {{
        0% {{ opacity: 0; transform: scale(0.75); transform-box: fill-box; transform-origin: center; }}
        100% {{ opacity: 1; transform: scale(1); transform-box: fill-box; transform-origin: center; }}
      }}
      {css_joined}
    </style>
  </defs>

  <!-- Terminal Card Frame -->
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>

  <!-- Top Window Bar -->
  <path d="M 1 13 A 12 12 0 0 1 13 1 L {width - 13} 1 A 12 12 0 0 1 {width - 1} 13 L {width - 1} 36 L 1 36 Z" fill="#161b22"/>
  <line x1="1" y1="36" x2="{width - 1}" y2="36" stroke="#30363d" stroke-width="1"/>

  <!-- Traffic Lights -->
  <circle cx="22" cy="18.5" r="5.5" fill="#ff5f56"/>
  <circle cx="40" cy="18.5" r="5.5" fill="#ffbd2e"/>
  <circle cx="58" cy="18.5" r="5.5" fill="#27c93f"/>
  <text x="{width // 2}" y="23" text-anchor="middle" class="mono" font-size="11.5" fill="#8b949e">gabin@github: ~/contributions (auto-refreshed daily)</text>

  <!-- Shell Command Prompt & Summary Stats -->
  <text x="24" y="62" class="mono" font-size="12.5">
    <tspan fill="#7ee787">gabin@github</tspan><tspan fill="#8b949e">:</tspan><tspan fill="#58a6ff">~</tspan><tspan fill="#8b949e">$ </tspan><tspan fill="#e6edf3">./contributions.sh --user {html.escape(user)} --heatmap</tspan>
  </text>
  <text x="{width - 24}" y="62" text-anchor="end" class="mono" font-size="12">
    <tspan fill="#39d353" font-weight="700">{total}</tspan><tspan fill="#8b949e"> contributions (last yr)  •  Longest streak: </tspan><tspan fill="#79c0ff" font-weight="600">{longest_streak}d</tspan><tspan fill="#8b949e">  •  Current: </tspan><tspan fill="#7ee787" font-weight="600">{current_streak}d</tspan>
  </text>

  <!-- Month & Day Labels -->
  {months_joined}
  {dows_joined}

  <!-- Animated 53-Week Heatmap Grid -->
{cols_joined}

  <!-- Footer Status & Legend -->
  <text x="56" y="{legend_y + 9}" class="mono" font-size="10.5" fill="#484f58">
    [cron: daily auto-update via GitHub Actions • synced {html.escape(updated_date)}]
  </text>
  {legend_joined}
</svg>
"""
    return svg


def main():
    if not DATA_PATH.exists():
        from fetch_contributions import main as fetch_main
        fetch_main()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    svg_content = render_heatmap_svg(data)
    OUTPUT_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Generated {OUTPUT_PATH} ({len(svg_content)} bytes)")


if __name__ == "__main__":
    main()

