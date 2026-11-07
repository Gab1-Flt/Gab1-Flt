#!/usr/bin/env python3
"""
Generate a sleek, animated Neofetch-style terminal SVG info card (info-card.svg)
for the GitHub Profile README.
"""

import html
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "info-card.svg"

HOST_USER = "gabin"
HOST_DOMAIN = "github"
PROMPT_CMD = "neofetch --config profile.conf"

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


def make_info_card_svg() -> str:
    width = 520
    height = 490

    lines_svg = []
    css_rules = []

    # Base Y after window bar and command prompt
    y = 92
    line_height = 22
    step_idx = 0

    # Header: gabin@github
    delay = 0.25
    css_rules.append(
        f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
    )
    lines_svg.append(
        f'  <g class="l{step_idx}">'
        f'<text x="28" y="{y}" class="mono bold" font-size="15">'
        f'<tspan fill="#58a6ff">{html.escape(HOST_USER)}</tspan>'
        f'<tspan fill="#8b949e">@</tspan>'
        f'<tspan fill="#7ee787">{html.escape(HOST_DOMAIN)}</tspan>'
        f'<tspan fill="#8b949e">  (Gabin Flotat)</tspan>'
        f"</text></g>"
    )
    y += 18
    step_idx += 1

    # Separator line under header
    delay = 0.25 + step_idx * 0.08
    css_rules.append(
        f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
    )
    lines_svg.append(
        f'  <g class="l{step_idx}">'
        f'<text x="28" y="{y}" class="mono" font-size="13" fill="#484f58">'
        f"────────────────────────────────────────────────────────"
        f"</text></g>"
    )
    y += 22
    step_idx += 1

    for key, val, color in ROWS:
        delay = 0.25 + step_idx * 0.08
        css_rules.append(
            f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
        )
        if key == "SEP":
            lines_svg.append(
                f'  <g class="l{step_idx}">'
                f'<line x1="28" y1="{y - 8}" x2="{width - 28}" y2="{y - 8}" stroke="#21262d" stroke-width="1" stroke-dasharray="4 4"/>'
                f"</g>"
            )
            y += 10
        else:
            key_padded = f"{key}:"
            lines_svg.append(
                f'  <g class="l{step_idx}">'
                f'<text x="28" y="{y}" class="mono" font-size="13">'
                f'<tspan fill="{color}" font-weight="600">{html.escape(key_padded)}</tspan>'
                f"</text>"
                f'<text x="148" y="{y}" class="mono" font-size="13" fill="#e6edf3">'
                f"{html.escape(val)}"
                f"</text>"
                f"</g>"
            )
            y += line_height
        step_idx += 1

    # Neofetch terminal ANSI color swatches
    y += 10
    delay = 0.25 + step_idx * 0.08
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
    sx = 28
    for c in palette_colors:
        swatches.append(
            f'<rect x="{sx}" y="{y - 11}" width="22" height="14" rx="3" fill="{c}"/>'
        )
        sx += 28
    lines_svg.append(f'  <g class="l{step_idx}">' + "".join(swatches) + "</g>")
    y += 28
    step_idx += 1

    # Active prompt with blinking cursor at the bottom
    delay = 0.25 + step_idx * 0.08
    css_rules.append(
        f".l{step_idx} {{ opacity: 0; animation: fadeSlide 0.35s ease forwards {delay:.2f}s; }}"
    )
    lines_svg.append(
        f'  <g class="l{step_idx}">'
        f'<text x="28" y="{y}" class="mono" font-size="13">'
        f'<tspan fill="#7ee787">gabin@github</tspan>'
        f'<tspan fill="#8b949e">:</tspan>'
        f'<tspan fill="#58a6ff">~</tspan>'
        f'<tspan fill="#8b949e">$ </tspan>'
        f"</text>"
        f'<rect x="150" y="{y - 11}" width="8" height="14" fill="#58a6ff" class="cursor"/>'
        f"</g>"
    )

    css_joined = "\n      ".join(css_rules)
    lines_joined = "\n".join(lines_svg)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <style>
      .mono {{
        font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      }}
      .bold {{
        font-weight: 700;
      }}
      @keyframes fadeSlide {{
        0% {{ opacity: 0; transform: translateY(4px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
      }}
      @keyframes blink {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
      }}
      .cursor {{
        animation: blink 1.1s steps(1) infinite;
      }}
      {css_joined}
    </style>
  </defs>

  <!-- Outer Terminal Window -->
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>

  <!-- Top Window Title Bar -->
  <path d="M 1 13 A 12 12 0 0 1 13 1 L {width - 13} 1 A 12 12 0 0 1 {width - 1} 13 L {width - 1} 38 L 1 38 Z" fill="#161b22"/>
  <line x1="1" y1="38" x2="{width - 1}" y2="38" stroke="#30363d" stroke-width="1"/>

  <!-- Window Traffic Light Dots -->
  <circle cx="22" cy="19.5" r="6" fill="#ff5f56"/>
  <circle cx="42" cy="19.5" r="6" fill="#ffbd2e"/>
  <circle cx="62" cy="19.5" r="6" fill="#27c93f"/>

  <!-- Window Title -->
  <text x="{width // 2}" y="24" text-anchor="middle" class="mono" font-size="12" fill="#8b949e">gabin@github: ~ (zsh)</text>

  <!-- Initial Command Prompt -->
  <text x="28" y="64" class="mono" font-size="13">
    <tspan fill="#7ee787">gabin@github</tspan><tspan fill="#8b949e">:</tspan><tspan fill="#58a6ff">~</tspan><tspan fill="#8b949e">$ </tspan><tspan fill="#e6edf3">{html.escape(PROMPT_CMD)}</tspan>
  </text>

  <!-- Neofetch Content Rows -->
{lines_joined}
</svg>
"""
    return svg


def main():
    svg_content = make_info_card_svg()
    OUTPUT_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Generated {OUTPUT_PATH} ({len(svg_content)} bytes)")


if __name__ == "__main__":
    main()

