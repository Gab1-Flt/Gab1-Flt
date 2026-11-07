#!/usr/bin/env python3
"""
Convert preprocessed portrait (source-prepped.png) into an animated monochrome
terminal ASCII portrait SVG (gabin-ascii.svg).
"""

import html
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "source-prepped.png"
OUTPUT_SVG = ROOT / "gabin-ascii.svg"
PREVIEW_PNG = ROOT / "ascii-preview.png"

# High-precision 16-step ASCII density ramp from dark/sparse to bright/dense
ASCII_RAMP = " .`',-~:;+=*#%@$"


def image_to_ascii_grid(
    img_path: Path, cols: int = 88, rows: int = 54
) -> tuple[list[str], np.ndarray]:
    """
    Convert RGBA image into a (rows x cols) grid of ASCII characters and normalized brightness.
    """
    im = Image.open(img_path).convert("RGBA")
    arr = np.array(im)

    # Crop tightly around non-transparent subject with a balanced aspect margin
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 32)
    if len(ys) > 0 and len(xs) > 0:
        y0 = max(0, int(ys.min()) - 8)
        y1 = min(arr.shape[0], int(ys.max()) + 2)
        x0 = max(0, int(xs.min()) - 14)
        x1 = min(arr.shape[1], int(xs.max()) + 14)
        im = im.crop((x0, y0, x1, y1))

    # Resize to (cols, rows) using Lanczos resampling
    im_small = im.resize((cols, rows), Image.Resampling.LANCZOS)
    small_arr = np.array(im_small, dtype=np.float32)

    lum = small_arr[:, :, 0]
    a = small_arr[:, :, 3] / 255.0

    n_chars = len(ASCII_RAMP)

    lines: list[str] = []
    norm_grid = np.zeros((rows, cols), dtype=np.float32)

    for r in range(rows):
        row_chars = []
        for c in range(cols):
            if a[r, c] < 0.30:
                row_chars.append(" ")
                norm_grid[r, c] = 0.0
            else:
                val = np.clip((lum[r, c] / 255.0) * a[r, c], 0.0, 1.0)
                # Keep silhouette visible with at least '.' on dark shirt, while sunglasses lenses stay '.'
                idx = int(round(val * (n_chars - 1)))
                if idx == 0 and a[r, c] > 0.65:
                    idx = 1  # '.' so dark silhouette stays coherent against black terminal
                idx = max(0, min(n_chars - 1, idx))
                row_chars.append(ASCII_RAMP[idx])
                norm_grid[r, c] = val
        lines.append("".join(row_chars))

    return lines, norm_grid


def build_ascii_svg(lines: list[str], static: bool = False) -> str:
    width = 380
    height = 490
    cols = len(lines[0]) if lines else 88
    rows = len(lines)

    start_x = 16
    start_y = 80
    row_height = 7.1
    font_size = 6.2
    target_text_width = width - 2 * start_x  # 348px across 88 chars (~3.95px/char)

    svg_rows = []
    css_rows = []

    for r_idx, line in enumerate(lines):
        y = start_y + r_idx * row_height
        delay = 0.12 + r_idx * 0.032

        if not static:
            css_rows.append(
                f".r{r_idx} {{ opacity: 0; animation: typeRow 0.18s steps(1) forwards {delay:.3f}s; }}"
            )
            cls_attr = f' class="mono r{r_idx}"'
        else:
            cls_attr = ' class="mono"'

        if line.strip() == "":
            continue

        # Escape XML entities and preserve spaces with non-breaking spaces for exact column alignment
        escaped = html.escape(line).replace(" ", "&#160;")
        svg_rows.append(
            f'  <text x="{start_x}" y="{y:.1f}"{cls_attr} font-size="{font_size}" '
            f'fill="#c9d1d9" textLength="{target_text_width}" lengthAdjust="spacing">{escaped}</text>'
        )

    css_joined = "\n      ".join(css_rows)
    rows_joined = "\n".join(svg_rows)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <style>
      .mono {{
        font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        font-variant-ligatures: none;
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
      .scan {{
        animation: scanline {0.12 + rows * 0.032 + 0.15:.2f}s linear forwards;
      }}
      {css_joined}
    </style>
  </defs>

  <!-- Terminal Window Frame -->
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>

  <!-- Top Window Title Bar -->
  <path d="M 1 13 A 12 12 0 0 1 13 1 L {width - 13} 1 A 12 12 0 0 1 {width - 1} 13 L {width - 1} 38 L 1 38 Z" fill="#161b22"/>
  <line x1="1" y1="38" x2="{width - 1}" y2="38" stroke="#30363d" stroke-width="1"/>

  <!-- Traffic Light Dots -->
  <circle cx="22" cy="19.5" r="6" fill="#ff5f56"/>
  <circle cx="42" cy="19.5" r="6" fill="#ffbd2e"/>
  <circle cx="62" cy="19.5" r="6" fill="#27c93f"/>

  <!-- Window Title -->
  <text x="{width // 2}" y="24" text-anchor="middle" class="mono" font-size="12" fill="#8b949e">portrait.sh — ascii</text>

  <!-- Command Prompt -->
  <text x="18" y="62" class="mono" font-size="12.5">
    <tspan fill="#7ee787">gabin@github</tspan><tspan fill="#8b949e">:</tspan><tspan fill="#58a6ff">~</tspan><tspan fill="#8b949e">$ </tspan><tspan fill="#e6edf3">./portrait.sh</tspan>
  </text>

  <!-- Terminal Scanline Bar During Typing -->
  <rect x="18" y="{start_y - 6}" width="{target_text_width}" height="2" fill="#58a6ff" class="scan"/>

  <!-- Monochrome ASCII Portrait Rows -->
{rows_joined}
</svg>
"""
    return svg


def save_png_preview(lines: list[str], out_png: Path) -> None:
    """Render a raster preview of the ASCII portrait for visual verification."""
    img = Image.new("RGB", (560, 620), color=(13, 17, 23))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("consola.ttf", 10)
    except Exception:
        font = ImageFont.load_default()

    y = 20
    for line in lines:
        draw.text((20, y), line, fill=(201, 209, 217), font=font)
        y += 10
    img.save(out_png)


def main():
    static = os.environ.get("STATIC", "0") == "1"
    lines, _ = image_to_ascii_grid(INPUT_PATH, cols=88, rows=54)
    svg_content = build_ascii_svg(lines, static=static)
    OUTPUT_SVG.write_text(svg_content, encoding="utf-8")
    save_png_preview(lines, PREVIEW_PNG)
    print(f"Generated {OUTPUT_SVG} ({len(svg_content)} bytes)")


if __name__ == "__main__":
    main()
