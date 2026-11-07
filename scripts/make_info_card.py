#!/usr/bin/env python3
"""
Generate the unified full-width terminal SVGs (880px wide, #0d1117 background):
1. whoami.svg   — Left-aligned 'whoami' terminal command box
2. neofetch.svg — Unified full-width box combining the animated ASCII portrait on the left
                  and the Neofetch system/profile card on the right
3. stack.svg    — Left-aligned './stack.sh --list' tree box with pixel-aligned colons
"""

import html
import os
from pathlib import Path
from make_ascii_svg import INPUT_PATH, image_to_ascii_grid

ROOT = Path(__file__).resolve().parent.parent
WHOAMI_PATH = ROOT / "whoami.svg"
NEOFETCH_PATH = ROOT / "neofetch.svg"
STACK_PATH = ROOT / "stack.svg"

HOST_USER = "gabin"
HOST_DOMAIN = "github"
PROMPT_CMD = "neofetch --ascii portrait.txt --config profile.conf"

# Structured Neofetch rows (Key, Value, Key Color)
ROWS = [
    ("Role", "Engineering Student", "#79c0ff"),
    ("Focus", "Full-Stack & Systems Developer", "#79c0ff"),
    ("Passions", "AI & Cybersecurity Enthusiast", "#79c0ff"),
    ("SEP", "", ""),
    ("Languages", "Python, TypeScript, C, Java, JS", "#d2a8ff"),
    ("Web & Data", "SQL, PHP, HTML5, CSS3", "#d2a8ff"),
    ("Frameworks", "React, Tailwind CSS", "#a5d6ff"),
    ("Hardware/IoT", "ESP32, LoRaWAN, FPGA", "#7ee787"),
    ("Boards", "Arduino, Raspberry Pi", "#7ee787"),
    ("Tools", "Git, Linux, Shell", "#ffa657"),
    ("SEP", "", ""),
    ("LinkedIn", "linkedin.com/in/gabin-flotat", "#58a6ff"),
    ("GitHub", "github.com/Gab1-Flt", "#58a6ff"),
    ("Status", "Building cool things • Open to connect", "#3fb950"),
]

STACK_ROWS = [
    ("├──", "Languages", "Python, TypeScript, C, Java, JavaScript, SQL, PHP, HTML, CSS", "#d2a8ff"),
    ("├──", "Frameworks", "React, Tailwind CSS", "#a5d6ff"),
    ("├──", "Hardware/IoT", "ESP32, LoRaWAN, FPGA, Arduino, Raspberry Pi", "#7ee787"),
    ("└──", "Tools", "Git, Linux, Shell", "#ffa657"),
]


def make_whoami_svg() -> str:
    width = 880
    height = 80
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <style>
      .mono {{
        font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      }}
      @keyframes fadeIn {{
        0% {{ opacity: 0; transform: translateY(3px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
      }}
      .line1 {{ opacity: 0; animation: fadeIn 0.3s ease forwards 0.05s; }}
      .line2 {{ opacity: 0; animation: fadeIn 0.35s ease forwards 0.22s; }}
    </style>
  </defs>

  <!-- Pitch-dark GitHub-matching Terminal Box -->
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>

  <!-- Line 1: Left-aligned terminal prompt -->
  <g class="line1">
    <text x="24" y="33" class="mono" font-size="13.5">
      <tspan fill="#7ee787" font-weight="600">gabin@github</tspan><tspan fill="#8b949e">:</tspan><tspan fill="#58a6ff" font-weight="600">~</tspan><tspan fill="#8b949e">$ </tspan><tspan fill="#e6edf3">whoami</tspan>
    </text>
  </g>

  <!-- Line 2: Left-aligned whoami output -->
  <g class="line2">
    <text x="24" y="58" class="mono" font-size="13.5">
      <tspan fill="#58a6ff" font-weight="700">&gt; </tspan><tspan fill="#e6edf3" font-weight="700">Gabin Flotat</tspan><tspan fill="#8b949e"> — </tspan><tspan fill="#c9d1d9">Engineering Student</tspan><tspan fill="#58a6ff"> • </tspan><tspan fill="#c9d1d9">Full-Stack &amp; Systems Developer</tspan><tspan fill="#58a6ff"> • </tspan><tspan fill="#c9d1d9">AI &amp; Cybersecurity Enthusiast</tspan>
    </text>
  </g>
</svg>
"""


def make_unified_neofetch_svg(ascii_lines: list[str], static: bool = False) -> str:
    width = 880
    height = 492

    # --- LEFT SIDE: ASCII PORTRAIT (x = 24 .. 372) ---
    rows = len(ascii_lines)
    ascii_x = 24
    ascii_y0 = 86
    row_height = 7.1
    font_size = 6.2
    target_text_width = 348  # 24 .. 372

    svg_ascii_rows = []
    css_rules = []

    for r_idx, line in enumerate(ascii_lines):
        y = ascii_y0 + r_idx * row_height
        delay = 0.12 + r_idx * 0.030
        if not static:
            css_rules.append(
                f".r{r_idx} {{ opacity: 0; animation: typeRow 0.16s steps(1) forwards {delay:.3f}s; }}"
            )
            cls_attr = f' class="mono r{r_idx}"'
        else:
            cls_attr = ' class="mono"'

        if line.strip() == "":
            continue

        escaped = html.escape(line).replace(" ", "&#160;")
        svg_ascii_rows.append(
            f'  <text x="{ascii_x}" y="{y:.1f}"{cls_attr} font-size="{font_size}" '
            f'fill="#c9d1d9" textLength="{target_text_width}" lengthAdjust="spacing">{escaped}</text>'
        )

    # --- RIGHT SIDE: NEOFETCH INFO (x = 416 .. 856) ---
    info_x = 416
    val_x = 540
    y = 94
    line_height = 22
    step_idx = 0
    lines_svg = []

    # Header: gabin@github (Gabin Flotat)
    delay = 0.20
    css_rules.append(
        f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
    )
    lines_svg.append(
        f'  <g class="l{step_idx}">'
        f'<text x="{info_x}" y="{y}" class="mono bold" font-size="15">'
        f'<tspan fill="#58a6ff">{html.escape(HOST_USER)}</tspan>'
        f'<tspan fill="#8b949e">@</tspan>'
        f'<tspan fill="#7ee787">{html.escape(HOST_DOMAIN)}</tspan>'
        f'<tspan fill="#8b949e">  (Gabin Flotat)</tspan>'
        f"</text></g>"
    )
    y += 18
    step_idx += 1

    # Separator under header
    delay = 0.20 + step_idx * 0.07
    css_rules.append(
        f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
    )
    lines_svg.append(
        f'  <g class="l{step_idx}">'
        f'<line x1="{info_x}" y1="{y - 5}" x2="{width - 28}" y2="{y - 5}" stroke="#30363d" stroke-width="1.2"/>'
        f"</g>"
    )
    y += 20
    step_idx += 1

    for key, val, color in ROWS:
        delay = 0.20 + step_idx * 0.07
        css_rules.append(
            f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
        )
        if key == "SEP":
            lines_svg.append(
                f'  <g class="l{step_idx}">'
                f'<line x1="{info_x}" y1="{y - 8}" x2="{width - 28}" y2="{y - 8}" stroke="#21262d" stroke-width="1" stroke-dasharray="4 4"/>'
                f"</g>"
            )
            y += 10
        else:
            key_padded = f"{key}:"
            lines_svg.append(
                f'  <g class="l{step_idx}">'
                f'<text x="{info_x}" y="{y}" class="mono" font-size="13">'
                f'<tspan fill="{color}" font-weight="600">{html.escape(key_padded)}</tspan>'
                f"</text>"
                f'<text x="{val_x}" y="{y}" class="mono" font-size="13" fill="#e6edf3">'
                f"{html.escape(val)}"
                f"</text>"
                f"</g>"
            )
            y += line_height
        step_idx += 1

    # ANSI 8-color swatches
    y += 10
    delay = 0.20 + step_idx * 0.07
    css_rules.append(
        f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
    )
    palette_colors = [
        "#484f58",
        "#ff7b72",
        "#3fb950",
        "#d29922",
        "#58a6ff",
        "#bc8cff",
        "#39c5cf",
        "#e6edf3",
    ]
    swatches = []
    sx = info_x
    for c in palette_colors:
        swatches.append(
            f'<rect x="{sx}" y="{y - 11}" width="24" height="14" rx="3" fill="{c}"/>'
        )
        sx += 30
    lines_svg.append(f'  <g class="l{step_idx}">' + "".join(swatches) + "</g>")
    y += 28
    step_idx += 1

    # Active prompt with blinking cursor
    delay = 0.20 + step_idx * 0.07
    css_rules.append(
        f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
    )
    lines_svg.append(
        f'  <g class="l{step_idx}">'
        f'<text x="{info_x}" y="{y}" class="mono" font-size="13">'
        f'<tspan fill="#7ee787">gabin@github</tspan>'
        f'<tspan fill="#8b949e">:</tspan>'
        f'<tspan fill="#58a6ff">~</tspan>'
        f'<tspan fill="#8b949e">$ </tspan>'
        f"</text>"
        f'<rect x="{info_x + 122}" y="{y - 11}" width="8" height="14" fill="#58a6ff" class="cursor"/>'
        f"</g>"
    )

    css_joined = "\n      ".join(css_rules)
    ascii_joined = "\n".join(svg_ascii_rows)
    info_joined = "\n".join(lines_svg)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <style>
      .mono {{
        font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        font-variant-ligatures: none;
      }}
      .bold {{
        font-weight: 700;
      }}
      @keyframes typeRow {{
        0% {{ opacity: 0; }}
        100% {{ opacity: 1; }}
      }}
      @keyframes scanline {{
        0% {{ transform: translateY(0px); opacity: 0.85; }}
        92% {{ transform: translateY({rows * row_height:.1f}px); opacity: 0.85; }}
        100% {{ transform: translateY({rows * row_height:.1f}px); opacity: 0; }}
      }}
      @keyframes fadeSlide {{
        0% {{ opacity: 0; transform: translateY(4px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
      }}
      @keyframes blink {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
      }}
      .scan {{
        animation: scanline {0.12 + rows * 0.030 + 0.15:.2f}s linear forwards;
      }}
      .cursor {{
        animation: blink 1.1s steps(1) infinite;
      }}
      {css_joined}
    </style>
  </defs>

  <!-- Unified Full-Width Terminal Window -->
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>

  <!-- Top Window Title Bar -->
  <path d="M 1 13 A 12 12 0 0 1 13 1 L {width - 13} 1 A 12 12 0 0 1 {width - 1} 13 L {width - 1} 36 L 1 36 Z" fill="#161b22"/>
  <line x1="1" y1="36" x2="{width - 1}" y2="36" stroke="#30363d" stroke-width="1"/>

  <!-- Traffic Light Dots -->
  <circle cx="22" cy="18.5" r="5.5" fill="#ff5f56"/>
  <circle cx="40" cy="18.5" r="5.5" fill="#ffbd2e"/>
  <circle cx="58" cy="18.5" r="5.5" fill="#27c93f"/>

  <!-- Window Title -->
  <text x="{width // 2}" y="23" text-anchor="middle" class="mono" font-size="11.5" fill="#8b949e">gabin@github: ~ — neofetch (zsh)</text>

  <!-- Top Shell Command Prompt -->
  <text x="24" y="62" class="mono" font-size="12.5">
    <tspan fill="#7ee787" font-weight="600">gabin@github</tspan><tspan fill="#8b949e">:</tspan><tspan fill="#58a6ff" font-weight="600">~</tspan><tspan fill="#8b949e">$ </tspan><tspan fill="#e6edf3">{html.escape(PROMPT_CMD)}</tspan>
  </text>

  <!-- Subtle Vertical Divider Between ASCII Portrait and Neofetch Info -->
  <line x1="394" y1="76" x2="394" y2="{height - 20}" stroke="#21262d" stroke-width="1"/>

  <!-- Scanline Bar on Left Portrait -->
  <rect x="{ascii_x}" y="{ascii_y0 - 6}" width="{target_text_width}" height="2" fill="#58a6ff" class="scan"/>

  <!-- Left Pane: Animated Monochrome ASCII Portrait -->
{ascii_joined}

  <!-- Right Pane: Animated Neofetch Info Rows -->
{info_joined}
</svg>
"""


def make_stack_svg() -> str:
    width = 880
    height = 148

    rows_svg = []
    css_rules = []
    y = 62
    for idx, (branch, category, items, color) in enumerate(STACK_ROWS):
        delay = 0.12 + idx * 0.08
        css_rules.append(
            f".s{idx} {{ opacity: 0; animation: fadeIn 0.3s ease forwards {delay:.2f}s; }}"
        )
        rows_svg.append(
            f'  <g class="s{idx}">'
            f'<text x="24" y="{y}" class="mono" font-size="13">'
            f'<tspan fill="#484f58">{html.escape(branch)} </tspan>'
            f'<tspan fill="{color}" font-weight="600">{html.escape(category)}</tspan>'
            f"</text>"
            f'<text x="176" y="{y}" class="mono" font-size="13">'
            f'<tspan fill="#58a6ff" font-weight="600">: </tspan>'
            f'<tspan fill="#e6edf3">{html.escape(items)}</tspan>'
            f"</text>"
            f"</g>"
        )
        y += 23

    css_joined = "\n      ".join(css_rules)
    rows_joined = "\n".join(rows_svg)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <style>
      .mono {{
        font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      }}
      @keyframes fadeIn {{
        0% {{ opacity: 0; transform: translateY(3px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
      }}
      {css_joined}
    </style>
  </defs>

  <!-- Pitch-dark GitHub-matching Terminal Box -->
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>

  <!-- Command Prompt -->
  <text x="24" y="34" class="mono" font-size="13.5">
    <tspan fill="#7ee787" font-weight="600">gabin@github</tspan><tspan fill="#8b949e">:</tspan><tspan fill="#58a6ff" font-weight="600">~</tspan><tspan fill="#8b949e">$ </tspan><tspan fill="#e6edf3">./stack.sh --list</tspan>
  </text>

  <!-- Left-aligned Tree Rows with Aligned Colons -->
{rows_joined}
</svg>
"""


def main():
    static = os.environ.get("STATIC", "0") == "1"
    ascii_lines, _ = image_to_ascii_grid(INPUT_PATH, cols=88, rows=54)

    whoami_svg = make_whoami_svg()
    WHOAMI_PATH.write_text(whoami_svg, encoding="utf-8")
    print(f"Generated {WHOAMI_PATH} ({len(whoami_svg)} bytes)")

    neofetch_svg = make_unified_neofetch_svg(ascii_lines, static=static)
    NEOFETCH_PATH.write_text(neofetch_svg, encoding="utf-8")
    print(f"Generated {NEOFETCH_PATH} ({len(neofetch_svg)} bytes)")

    stack_svg = make_stack_svg()
    STACK_PATH.write_text(stack_svg, encoding="utf-8")
    print(f"Generated {STACK_PATH} ({len(stack_svg)} bytes)")


if __name__ == "__main__":
    main()
