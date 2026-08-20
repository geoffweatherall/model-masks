#!/usr/bin/env python3
"""Split the regularized E2-S SVG into two separate cut files: E2 (the
squadron code, shared across this squadron's aircraft) and S (this
aircraft's own call letter, independent). Each gets its own mm-sized
canvas so it can be imported into Silhouette Studio on its own."""
import re

REPO = "/home/geoff/Projects/model-masks-workspace/model-masks"
SRC = f"{REPO}/masks/projects/bottisham-four/E2-S/svg/e2-s-regularized.svg"
SVG_DIR = f"{REPO}/masks/projects/bottisham-four/E2-S/svg"
MARGIN_MM = 1.5

svg = open(SRC).read()
paths = {}
for m in re.finditer(r'<path id="(\w+)" d="([^"]+)"', svg):
    name, d = m.group(1), m.group(2)
    pts = [tuple(map(float, p.split(","))) for p in re.findall(r'-?\d+\.\d+,-?\d+\.\d+', d)]
    paths[name] = (d, pts)

def write_group(filename, ids):
    all_pts = [p for name in ids for p in paths[name][1]]
    xs = [p[0] for p in all_pts]; ys = [p[1] for p in all_pts]
    ox, oy = min(xs) - MARGIN_MM, min(ys) - MARGIN_MM
    W = max(xs) - min(xs) + 2 * MARGIN_MM
    H = max(ys) - min(ys) + 2 * MARGIN_MM
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{H:.3f}mm" viewBox="0 0 {W:.3f} {H:.3f}">']
    for name in ids:
        d, pts = paths[name]
        shifted = "M " + " L ".join(f"{x-ox:.3f},{y-oy:.3f}" for x, y in pts) + " Z"
        lines.append(f'  <path id="{name}" d="{shifted}" fill="#000000"/>')
    lines.append('</svg>')
    out = f"{SVG_DIR}/{filename}"
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {filename}  ({W:.2f} x {H:.2f} mm)")

write_group("e2-regularized.svg", ["E", "2"])
write_group("s-regularized.svg", ["S"])
