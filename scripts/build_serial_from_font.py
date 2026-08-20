#!/usr/bin/env python3
"""Build the E2-S tail serial from the usaaf-serial-stencil.ttf font,
rather than hand-tracing/regularizing - the hand-built curve reconstruction
(Approach A/B) was a poor match. Reuses the calibration and per-digit
sizing already measured from the scan (24.0957 px/mm, 1.37mm digit gap,
per-digit widths), just swaps in the font's own clean glyph outlines
instead of custom geometry.
"""
import re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

REPO = "/home/geoff/Projects/model-masks-workspace/model-masks"
FONT_PATH = f"{REPO}/fonts/usaaf-serial-stencil.ttf"
OUT_SVG = f"{REPO}/masks/projects/bottisham-four/E2-S/svg/tail-serial-413926-font.svg"

H = 4.07          # canonical digit height (calculated earlier from the 18.8mm calibration)
GAP = 1.37         # mm, measured inter-digit gap from the scan
MARGIN = 0.3
DIGITS = "413926"
# measured digit widths in mm (from the scan, 24.0957 px/mm calibration)
DECAL_WIDTHS_MM = {
    "4": 2.283, "1": 0.539, "3": 2.283, "9": 2.283, "2": 2.283, "6": 2.324,
}

def parse_path(d):
    """Expand an SVGPathPen M/L/H/V/Z absolute-coordinate path into a LIST OF
    SUBPATHS (each a list of (x,y) points) - glyphs like "3","9","6" have
    multiple disconnected pieces (stencil gaps, separate counters), each
    starting with its own M, and treating them as one continuous polygon
    creates a spurious line cutting across the glyph. Also handles SVG's
    implicit-lineto shorthand (extra coordinate pairs after M/L with no
    repeated command letter)."""
    tokens = re.findall(r'[MLHVZ]|-?\d+(?:\.\d+)?', d)
    subpaths = []
    pts, i, cur, cmd = [], 0, (0.0, 0.0), None
    while i < len(tokens):
        tok = tokens[i]
        if tok in "MLHVZ":
            cmd = tok
            i += 1
            if cmd == 'M':
                if pts:
                    subpaths.append(pts)
                pts = []
                cmd = 'L'
                x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                cur = (x, y); pts.append(cur)
                continue
            if cmd == 'Z':
                continue
        if cmd == 'L':
            x, y = float(tokens[i]), float(tokens[i+1]); i += 2
            cur = (x, y); pts.append(cur)
        elif cmd == 'H':
            x = float(tokens[i]); i += 1
            cur = (x, cur[1]); pts.append(cur)
        elif cmd == 'V':
            y = float(tokens[i]); i += 1
            cur = (cur[0], y); pts.append(cur)
    if pts:
        subpaths.append(pts)
    return subpaths

font = TTFont(FONT_PATH)
glyphset = font.getGlyphSet()
cmap = font.getBestCmap()

def glyph_info(ch):
    gname = cmap[ord(ch)]
    glyph = glyphset[gname]
    bp = BoundsPen(glyphset)
    glyph.draw(bp)
    return glyph, bp.bounds, glyph.width

# reference cap height from "4" (same convention used throughout this project)
_, ref_bounds, _ = glyph_info("4")
cap_height_units = ref_bounds[3] - ref_bounds[1]  # 719
y_scale = H / cap_height_units

x_cursor = 0.0
entries = []
for ch in DIGITS:
    glyph, (x0, y0, x1, y1), adv = glyph_info(ch)
    pen = SVGPathPen(glyphset)
    glyph.draw(pen)
    subpaths = parse_path(pen.getCommands())

    glyph_w_units = x1 - x0
    x_scale = DECAL_WIDTHS_MM[ch] / glyph_w_units  # per-digit aspect correction, like the E2/S work

    def transform(px, py, x0=x0, x_scale=x_scale, origin_x=x_cursor):
        mm_x = (px - x0) * x_scale + origin_x
        mm_y = (cap_height_units - py) * y_scale  # flip: font baseline-up -> svg y-down
        return mm_x, mm_y

    d_parts = []
    for pts in subpaths:
        tpts = [transform(px, py) for px, py in pts]
        d_parts.append("M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in tpts) + " Z")
    d = " ".join(d_parts)
    entries.append((ch, d))
    x_cursor += DECAL_WIDTHS_MM[ch] + GAP

total_w = x_cursor - GAP

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w+2*MARGIN:.3f}mm" height="{H+2*MARGIN:.3f}mm" '
       f'viewBox="{-MARGIN:.3f} {-MARGIN:.3f} {total_w+2*MARGIN:.3f} {H+2*MARGIN:.3f}">']
for i, (ch, d) in enumerate(entries):
    d_shifted = re.sub(r'(-?\d+\.\d+),(-?\d+\.\d+)',
                        lambda m: f"{float(m.group(1))+MARGIN:.3f},{float(m.group(2))+MARGIN:.3f}", d)
    svg.append(f'  <path id="{ch}{i}" d="{d_shifted}" fill="#000000"/>')
svg.append('</svg>')

with open(OUT_SVG, "w") as f:
    f.write("\n".join(svg) + "\n")
print(f"wrote {OUT_SVG}  ({total_w+2*MARGIN:.3f} x {H+2*MARGIN:.3f} mm)")
