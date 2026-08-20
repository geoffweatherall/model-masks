#!/usr/bin/env python3
"""Trace the E2-S tail serial ("413926") from its decal scan crop into a
curve-preserving SVG, calibrated to a given real-world span.

Pipeline:
  1. Binarize the top-row crop and find each digit's fragments (a stencil
     font's gaps mean each digit is several disconnected blobs) via OpenCV,
     clustering fragments into 6 digits by x-position.
  2. Measure "left of first digit" to "right of last digit" in pixels, and
     calibrate against the given real-world span (REF_SPAN_MM).
  3. Run potrace on the same binarized crop for a smooth bezier trace (this
     digit font has real curves, unlike E2-S's straight-chamfer letters).
  4. Rewrite potrace's output SVG: crop the viewBox to the digit content
     (+ small margin) and set width/height in mm from the calibration - no
     path data needs touching, since potrace's own transform already maps
     1 output unit = 1 input pixel.

Requires potrace (`sudo apt install potrace`) on PATH.
"""
import subprocess
import re
import tempfile
import os
import cv2

REPO = "/home/geoff/Projects/model-masks-workspace/model-masks"
SRC_PNG = f"{REPO}/masks/projects/bottisham-four/E2-S/resources/decal-tail-serial-413926.png"
OUT_SVG = f"{REPO}/masks/projects/bottisham-four/E2-S/svg/tail-serial-413926-traced.svg"
ROW_HEIGHT = 135          # crop out just the top instance of the two duplicate rows
REF_SPAN_MM = 18.8        # user-measured: left edge of first digit to right edge of last
CROP_MARGIN_PX = 3
MIN_FRAGMENT_AREA = 150
DIGIT_GAP_PX = 8          # x-gap larger than this = a new digit, not a stencil break

def cluster_digits(img_path, row_height):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
    top_row = binary[0:row_height, :]
    contours, _ = cv2.findContours(top_row, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > MIN_FRAGMENT_AREA]
    boxes.sort(key=lambda b: b[0])
    digits, cur = [], [boxes[0]]
    for b in boxes[1:]:
        prev_right = max(bb[0] + bb[2] for bb in cur)
        if b[0] - prev_right > DIGIT_GAP_PX:
            digits.append(cur)
            cur = [b]
        else:
            cur.append(b)
    digits.append(cur)
    return digits

digits = cluster_digits(SRC_PNG, ROW_HEIGHT)
print(f"{len(digits)} digits found")
for i, d in enumerate(digits):
    x0 = min(b[0] for b in d); x1 = max(b[0]+b[2] for b in d)
    y0 = min(b[1] for b in d); y1 = max(b[1]+b[3] for b in d)
    print(f"  digit {i}: x=[{x0},{x1}] y=[{y0},{y1}]  ({len(d)} fragments)")

x0_first = min(b[0] for b in digits[0])
x1_last = max(b[0]+b[2] for b in digits[-1])
span_px = x1_last - x0_first
px_per_mm = span_px / REF_SPAN_MM
print(f"\nreference span: {span_px}px = {REF_SPAN_MM}mm given -> {px_per_mm:.4f} px/mm")

overall_y0 = min(min(b[1] for b in d) for d in digits)
overall_y1 = max(max(b[1]+b[3] for b in d) for d in digits)
height_mm = (overall_y1 - overall_y0) / px_per_mm
print(f"calculated height: {overall_y1-overall_y0}px = {height_mm:.3f}mm")

# --- potrace: smooth curve-preserving trace of the same crop ---
tmpdir = tempfile.mkdtemp(prefix="trace-tail-serial-")
pbm = os.path.join(tmpdir, "serial-bw.pbm")
raw_svg = os.path.join(tmpdir, "serial-potrace.svg")
subprocess.run(["convert", SRC_PNG, "-crop", f"620x{ROW_HEIGHT}+0+0", "+repage",
                 "-threshold", "47%", pbm], check=True)
subprocess.run(["potrace", "-s", "-x", "1", "-M", "0", "--turdsize", "5",
                 "-o", raw_svg, pbm], check=True)

# --- crop viewBox to content + margin, set mm size; leave path data as-is ---
x0 = x0_first - CROP_MARGIN_PX
y0 = overall_y0 - CROP_MARGIN_PX
x1 = x1_last + CROP_MARGIN_PX
y1 = overall_y1 + CROP_MARGIN_PX
w_px, h_px = x1 - x0, y1 - y0
w_mm, h_mm = w_px / px_per_mm, h_px / px_per_mm

src = open(raw_svg).read()
new_header = (f'<svg version="1.0" xmlns="http://www.w3.org/2000/svg"\n'
              f' width="{w_mm:.3f}mm" height="{h_mm:.3f}mm" viewBox="{x0} {y0} {w_px} {h_px}"\n'
              f' preserveAspectRatio="xMidYMid meet">')
out = re.sub(r'<svg version.*?preserveAspectRatio="xMidYMid meet">', new_header, src, flags=re.S)
with open(OUT_SVG, "w") as f:
    f.write(out)
print(f"\nwrote {OUT_SVG}  ({w_mm:.3f} x {h_mm:.3f} mm, viewBox origin ({x0},{y0}))")

import shutil
shutil.rmtree(tmpdir, ignore_errors=True)
