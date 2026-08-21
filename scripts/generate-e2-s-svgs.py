#!/usr/bin/env python3
"""Generate two comparison SVGs for the E2-S squadron code:
  1) e2-s-traced.svg   - straight-line polygon trace of the decal scan
  2) e2-s-font.svg     - reconstruction from the AmarilloUSAF font, with
                          per-letter width corrected to match the decal's
                          aspect ratio, and E-2 spacing matched to the decal
Both are sized in real-world mm (11.5mm canonical letter height), so a
straight SVG import into Silhouette Studio comes in at the correct size.
"""
import re
import cv2
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

REPO = "/home/geoff/Projects/model-masks-workspace/model-masks"
DECAL_IMG = f"{REPO}/masks/projects/bottisham-four/E2-S/resources/decal-e2-s-code.png"
# amarillo-usaf.ttf is registered shareware, not clearly open, so it lives in
# the private sibling repo, not this one - see model-masks/CLAUDE.md
FONT_PATH = "/home/geoff/Projects/model-masks-workspace/model-fonts/fonts-proprietary/amarillo-usaf.ttf"
OUT_DIR = f"{REPO}/masks/projects/bottisham-four/E2-S/svg"
CANONICAL_HEIGHT_MM = 11.5
MARGIN_MM = 1.5

# ---------------------------------------------------------------------------
# 1) Trace the decal scan into simplified straight-line polygons
# ---------------------------------------------------------------------------
img = cv2.imread(DECAL_IMG)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
# top row only (830x420 excludes the duplicate row + circled item numbers)
binary = binary[0:420, 0:830]
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = [c for c in contours if cv2.contourArea(c) > 5000]
contours.sort(key=lambda c: cv2.boundingRect(c)[0])
assert len(contours) == 3, f"expected 3 letters (E,2,S), found {len(contours)}"

letters_px = []
for c, name in zip(contours, ["E", "2", "S"]):
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.004 * peri, True).reshape(-1, 2)
    x, y, w, h = cv2.boundingRect(c)
    letters_px.append({"name": name, "points": approx, "bbox": (x, y, w, h)})

# canonical scale: E's pixel height maps to CANONICAL_HEIGHT_MM
E = letters_px[0]
px_to_mm = CANONICAL_HEIGHT_MM / E["bbox"][3]
print(f"decal calibration: {1/px_to_mm:.4f} px/mm (E height {E['bbox'][3]}px -> {CANONICAL_HEIGHT_MM}mm)")

min_x = min(L["bbox"][0] for L in letters_px)
min_y = min(L["bbox"][1] for L in letters_px)
max_x = max(L["bbox"][0] + L["bbox"][2] for L in letters_px)
max_y = max(L["bbox"][1] + L["bbox"][3] for L in letters_px)
traced_w = (max_x - min_x) * px_to_mm + 2 * MARGIN_MM
traced_h = (max_y - min_y) * px_to_mm + 2 * MARGIN_MM

def px_point_to_mm(px, py):
    return ((px - min_x) * px_to_mm + MARGIN_MM, (py - min_y) * px_to_mm + MARGIN_MM)

traced_paths = []
for L in letters_px:
    pts = [px_point_to_mm(x, y) for x, y in L["points"]]
    d = "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in pts) + " Z"
    traced_paths.append((L["name"], d))
    x, y, w, h = L["bbox"]
    print(f"  {L['name']}: {len(pts)} vertices, {w*px_to_mm:.3f}mm wide")

gap_e2_px = letters_px[1]["bbox"][0] - (letters_px[0]["bbox"][0] + letters_px[0]["bbox"][2])
gap_2s_px = letters_px[2]["bbox"][0] - (letters_px[1]["bbox"][0] + letters_px[1]["bbox"][2])
print(f"  gap E->2: {gap_e2_px*px_to_mm:.3f}mm   gap 2->S: {gap_2s_px*px_to_mm:.3f}mm (reference only)")

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{traced_w:.3f}mm" height="{traced_h:.3f}mm" '
       f'viewBox="0 0 {traced_w:.3f} {traced_h:.3f}">']
for name, d in traced_paths:
    svg.append(f'  <path id="{name}" d="{d}" fill="#000000"/>')
svg.append('</svg>')
with open(f"{OUT_DIR}/e2-s-traced.svg", "w") as f:
    f.write("\n".join(svg) + "\n")
print(f"wrote e2-s-traced.svg  ({traced_w:.2f} x {traced_h:.2f} mm)")

decal_widths_mm = {L["name"]: L["bbox"][2] * px_to_mm for L in letters_px}
gap_e2_mm = gap_e2_px * px_to_mm

# ---------------------------------------------------------------------------
# 2) Font-based reconstruction, width-corrected to the decal's aspect ratio
# ---------------------------------------------------------------------------
font = TTFont(FONT_PATH)
glyphset = font.getGlyphSet()
cmap = font.getBestCmap()

def glyph_info(ch):
    gname = cmap[ord(ch)]
    glyph = glyphset[gname]
    bp = BoundsPen(glyphset)
    glyph.draw(bp)
    x0, y0, x1, y1 = bp.bounds
    return glyph, (x0, y0, x1, y1), glyph.width

def parse_path(d):
    """Expand an SVGPathPen M/L/H/V/Z absolute-coordinate path into a list of
    (x,y) points. Handles implicit command repetition per the SVG spec: extra
    coordinate pairs after M or L (with no repeated command letter) are
    implicit further linetos - e.g. "M450 100 350 0H150" is moveto(450,100),
    LINETO(350,0), H150."""
    tokens = re.findall(r'[MLHVZ]|-?\d+(?:\.\d+)?', d)
    pts, i, cur, cmd = [], 0, (0.0, 0.0), None
    while i < len(tokens):
        tok = tokens[i]
        if tok in "MLHVZ":
            cmd = tok
            i += 1
            if cmd == 'M':
                cmd = 'L'  # subsequent implicit pairs after the first M are linetos
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
    return pts

E_glyph, E_bounds, E_adv = glyph_info("E")
cap_height_units = E_bounds[3] - E_bounds[1]  # 600
y_scale = CANONICAL_HEIGHT_MM / cap_height_units

letters_font = []
x_cursor_mm = 0.0
prev_bounds = None
prev_adv = None
for i, ch in enumerate(["E", "2", "S"]):
    glyph, (x0, y0, x1, y1), adv = glyph_info(ch)
    from fontTools.pens.svgPathPen import SVGPathPen
    pen = SVGPathPen(glyphset)
    glyph.draw(pen)
    pts = parse_path(pen.getCommands())

    glyph_w_units = x1 - x0
    x_scale = decal_widths_mm[ch] / glyph_w_units  # per-letter aspect correction

    if i == 0:
        origin_x = 0.0
    elif ch == "2":
        origin_x = decal_widths_mm["E"] + gap_e2_mm
    else:  # "S": independent - use the font's own natural advance-based gap
        natural_gap_units = (prev_adv - prev_bounds[2]) + (x0)  # right-side-bearing(prev) + left-side-bearing(this)
        natural_gap_mm = natural_gap_units * y_scale
        origin_x = x_cursor_mm + natural_gap_mm

    def transform(px, py, x0=x0, x_scale=x_scale, origin_x=origin_x):
        mm_x = (px - x0) * x_scale + origin_x
        mm_y = (cap_height_units - py) * y_scale  # flip: font baseline-up -> svg y-down
        return mm_x, mm_y

    tpts = [transform(px, py) for px, py in pts]
    d = "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in tpts) + " Z"
    letters_font.append((ch, d))

    x_cursor_mm = origin_x + decal_widths_mm[ch]
    prev_bounds = (x0, y0, x1, y1)
    prev_adv = adv
    print(f"  font {ch}: x_scale={x_scale:.5f} origin_x={origin_x:.3f}mm width={decal_widths_mm[ch]:.3f}mm")

font_w = x_cursor_mm + 2 * MARGIN_MM
font_h = CANONICAL_HEIGHT_MM + 2 * MARGIN_MM

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{font_w:.3f}mm" height="{font_h:.3f}mm" '
       f'viewBox="0 0 {font_w:.3f} {font_h:.3f}">']
for name, d in letters_font:
    # shift by MARGIN_MM in both axes
    d_shifted = re.sub(r'(-?\d+\.\d+),(-?\d+\.\d+)',
                        lambda m: f"{float(m.group(1))+MARGIN_MM:.3f},{float(m.group(2))+MARGIN_MM:.3f}", d)
    svg.append(f'  <path id="{name}" d="{d_shifted}" fill="#000000"/>')
svg.append('</svg>')
with open(f"{OUT_DIR}/e2-s-font.svg", "w") as f:
    f.write("\n".join(svg) + "\n")
print(f"wrote e2-s-font.svg  ({font_w:.2f} x {font_h:.2f} mm)")
