#!/usr/bin/env python3
"""
Preprocess a portrait photo for monochrome ASCII conversion:
1. Cleanly removes background (isolating subject onto transparent canvas)
2. Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) and local detail
   enhancement so hair, sunglasses, facial features, shirt, phone, and hand pop out
   crisply instead of turning into a flat dark blob.
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "source-photo.jpg"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "source-prepped.png"


def clahe_2d(img_uint8: np.ndarray, grid_size: int = 8, clip_limit: float = 2.5) -> np.ndarray:
    """
    Pure NumPy implementation of Contrast Limited Adaptive Histogram Equalization (CLAHE)
    with bilinear tile interpolation.
    """
    H, W = img_uint8.shape
    ny = grid_size
    nx = grid_size
    tile_h = H / ny
    tile_w = W / nx

    luts = np.zeros((ny, nx, 256), dtype=np.float32)
    for iy in range(ny):
        y0 = int(round(iy * tile_h))
        y1 = int(round((iy + 1) * tile_h))
        for ix in range(nx):
            x0 = int(round(ix * tile_w))
            x1 = int(round((ix + 1) * tile_w))
            tile = img_uint8[y0:y1, x0:x1]
            hist, _ = np.histogram(tile, bins=256, range=(0, 256))
            hist = hist.astype(np.float32)

            # Clip histogram
            limit = max(1.0, clip_limit * tile.size / 256.0)
            excess = np.maximum(0.0, hist - limit)
            total_excess = np.sum(excess)
            hist = np.minimum(hist, limit) + (total_excess / 256.0)

            cdf = np.cumsum(hist)
            cdf_min = cdf[cdf > 0][0] if np.any(cdf > 0) else 0.0
            denom = max(1.0, tile.size - cdf_min)
            lut = np.clip((cdf - cdf_min) / denom * 255.0, 0.0, 255.0)
            luts[iy, ix] = lut

    # Bilinear interpolation across tile centers
    yy = (np.arange(H, dtype=np.float32) + 0.5) / tile_h - 0.5
    xx = (np.arange(W, dtype=np.float32) + 0.5) / tile_w - 0.5

    iy0 = np.clip(np.floor(yy).astype(np.int32), 0, ny - 1)
    iy1 = np.clip(iy0 + 1, 0, ny - 1)
    wy = np.clip(yy - iy0, 0.0, 1.0)[:, None]

    ix0 = np.clip(np.floor(xx).astype(np.int32), 0, nx - 1)
    ix1 = np.clip(ix0 + 1, 0, nx - 1)
    wx = np.clip(xx - ix0, 0.0, 1.0)[None, :]

    Y_idx, X_idx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    val = img_uint8[Y_idx, X_idx]

    v00 = luts[iy0[:, None], ix0[None, :], val]
    v01 = luts[iy0[:, None], ix1[None, :], val]
    v10 = luts[iy1[:, None], ix0[None, :], val]
    v11 = luts[iy1[:, None], ix1[None, :], val]

    top = v00 * (1.0 - wx) + v01 * wx
    bot = v10 * (1.0 - wx) + v11 * wx
    res = top * (1.0 - wy) + bot * wy
    return np.clip(res, 0, 255).astype(np.uint8)


def extract_foreground_mask(arr: np.ndarray) -> np.ndarray:
    """
    Segment the portrait subject from the slatted wall and window background.
    """
    H, W, _ = arr.shape
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.299 * R + 0.587 * G + 0.114 * B
    warmth = R - B

    # Smooth horizontally only across 5px to bridge thin 2-3px dark wall grooves
    lum_h_smooth = ndimage.median_filter(lum, size=(1, 7))
    warmth_h_smooth = ndimage.median_filter(warmth, size=(1, 7))

    # Background wall & window are neutral (low warmth) and medium-to-bright luminance
    bg_candidate = (warmth_h_smooth < 15.0) & (lum_h_smooth > 68.0)

    # Protect the torso/shoulders/backpack silhouette region from being eaten by background flood
    yy, xx = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")
    torso_protect = np.zeros((H, W), dtype=bool)
    for y in range(405, H):
        t = min(1.0, (y - 405) / 140.0)
        # Left shoulder curves from base of neck (x=286) out to left arm (x=148)
        x_left = int(286 - 138 * (t ** 0.68))
        # Right shoulder curves from base of neck (x=426) out to right arm (x=608)
        x_right = int(426 + 182 * (t ** 0.68))
        torso_protect[y, x_left:x_right] = True

    # Protect internal head core (sunglasses lenses & frames inside face boundary)
    head_core = ((xx - 346) / 86.0) ** 2 + ((yy - 255) / 95.0) ** 2 <= 1.0
    bg_candidate = bg_candidate & (~torso_protect) & (~head_core)

    # Flood fill background from top, left, and right image borders
    seed = np.zeros((H, W), dtype=bool)
    seed[0, :] = True
    seed[:, 0] = True
    seed[:, -1] = True
    bg_mask = ndimage.binary_propagation(seed, mask=bg_candidate)

    # Explicit outer background zones outside subject bounding silhouette
    outer_bg = np.zeros((H, W), dtype=bool)
    outer_bg[:78, :] = True
    outer_bg[:, :142] = True
    outer_bg[:, 618:] = True
    outer_bg[:180, :222] = True
    outer_bg[:180, 470:] = True
    # Around temples / ears (y=180..315)
    outer_bg[180:315, :244] = True
    outer_bg[180:315, 448:] = True
    # Around lower jaw & neck (y=315..405), any low-warmth neutral gray is background wall
    jaw_neck_zone = (yy >= 295) & (yy <= 415) & ((xx < 292) | (xx > 422))
    jaw_neck_wall = jaw_neck_zone & (warmth < 16.0)

    fg_mask = ~(bg_mask | outer_bg | jaw_neck_wall)

    # Horizontal opening to remove any remaining thin vertical wall groove spikes
    fg_mask = ndimage.binary_opening(fg_mask, structure=np.ones((1, 9)))
    fg_mask = ndimage.binary_closing(fg_mask, structure=np.ones((7, 7)))

    # Keep largest connected component and fill internal holes
    labeled, num = ndimage.label(fg_mask)
    if num > 0:
        sizes = ndimage.sum(fg_mask, labeled, range(1, num + 1))
        largest = np.argmax(sizes) + 1
        fg_mask = labeled == largest
    fg_mask = ndimage.binary_fill_holes(fg_mask)

    return fg_mask


def prep_photo(input_path: Path, output_path: Path) -> None:
    im = Image.open(input_path).convert("RGB")
    arr = np.array(im, dtype=np.float32)
    H, W, _ = arr.shape

    fg_mask = extract_foreground_mask(arr)

    # Compute luminance
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = (0.299 * R + 0.587 * G + 0.114 * B).astype(np.uint8)

    # Apply CLAHE for strong local contrast (brings out hair texture, sunglasses rims,
    # shirt folds, backpack straps, iPhone camera bump, and hand/rings)
    enhanced = clahe_2d(lum, grid_size=8, clip_limit=2.8).astype(np.float32)

    # Blend 75% CLAHE + 25% original luminance for natural tonal hierarchy
    blended = 0.75 * enhanced + 0.25 * lum.astype(np.float32)

    # Strong edge sharpening (unsharp mask) so sunglasses frames, nose, lips, hair strands,
    # iPhone border, camera bump, and fingers have crisp high-contrast boundaries
    blurred = ndimage.gaussian_filter(blended, sigma=2.2)
    sharpened = np.clip(blended + 1.35 * (blended - blurred), 0, 255)

    # Deepen darks (sunglasses lenses, shirt shadows) and brighten highlights (skin, hair, hand)
    # using an S-curve contrast stretch
    norm = sharpened / 255.0
    s_curve = np.clip((norm - 0.14) / 0.78, 0.0, 1.0) ** 1.12
    sharpened = (s_curve * 255.0).astype(np.uint8)

    # Soften alpha edge by 1px for clean anti-aliased boundary
    alpha = ndimage.gaussian_filter(fg_mask.astype(np.float32), sigma=0.8)
    alpha_u8 = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    alpha_u8[alpha_u8 < 64] = 0

    out_rgba = np.zeros((H, W, 4), dtype=np.uint8)
    out_rgba[:, :, 0] = sharpened
    out_rgba[:, :, 1] = sharpened
    out_rgba[:, :, 2] = sharpened
    out_rgba[:, :, 3] = alpha_u8

    # Tight crop slightly to frame portrait nicely
    out_img = Image.fromarray(out_rgba, mode="RGBA")
    out_img.save(output_path)
    print(f"Saved preprocessed portrait to {output_path} ({W}x{H})")


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    prep_photo(in_path, out_path)


if __name__ == "__main__":
    main()
