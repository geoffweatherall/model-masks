#!/usr/bin/env python3
"""Regularize the traced E2-S letters (e2-s-traced.svg) into an idealized
version: every edge snapped to an exact angle (0/45/90/135deg), every rail
(the line each edge lies on) snapped to a consistent position shared with
other edges on the same rail, and every stroke-width gap forced to one
canonical value. Vertices are then re-solved as intersections of their two
neighbouring (now-exact) edge lines - this is the general method used for
all three letters, not a per-letter special case, so it can't introduce the
kind of asymmetry a hand-tuned shape would.
"""
import re
import math

REPO = "/home/geoff/Projects/model-masks-workspace/model-masks"
TRACED_SVG = f"{REPO}/masks/projects/bottisham-four/E2-S/svg/e2-s-traced.svg"
OUT_SVG = f"{REPO}/masks/projects/bottisham-four/E2-S/svg/e2-s-regularized.svg"

CANONICAL_STROKE = 1.60   # mm - single stroke width forced across all letters
RAIL_CLUSTER_TOL = 0.20   # mm - edges within this offset of each other share a rail
STROKE_PAIR_MIN = 1.30    # mm - gap range that gets recognised as "this is a stroke"
STROKE_PAIR_MAX = 1.90
MARGIN_MM = 1.5

def load_letters(svg_path):
    svg = open(svg_path).read()
    letters = {}
    for m in re.finditer(r'<path id="(\w+)" d="([^"]+)"', svg):
        name, d = m.group(1), m.group(2)
        pts = [tuple(map(float, p.split(","))) for p in re.findall(r'-?\d+\.\d+,-?\d+\.\d+', d)]
        letters[name] = pts
    return letters

def snap_angle(deg):
    for a in (0, 45, 90, 135, 180):
        if abs(deg - a) <= 15:
            return a % 180
    return deg

def edge_offset(p, angle_deg):
    """Perpendicular offset of point p from the origin, along the normal of a
    line running at angle_deg. Two collinear edges at the same angle share
    this value exactly."""
    theta = math.radians(angle_deg)
    nx, ny = -math.sin(theta), math.cos(theta)
    return p[0]*nx + p[1]*ny

def cluster(values, tol):
    """Greedy 1D clustering: sort, group points within tol of the running
    cluster mean, replace each with its cluster's mean."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    clusters = []  # list of [sum, count, members(list of original idx)]
    for i in order:
        v = values[i]
        if clusters and abs(v - clusters[-1][0]/clusters[-1][1]) <= tol:
            clusters[-1][0] += v
            clusters[-1][1] += 1
            clusters[-1][2].append(i)
        else:
            clusters.append([v, 1, [i]])
    snapped = [None]*len(values)
    for s, c, members in clusters:
        mean = s / c
        for i in members:
            snapped[i] = mean
    return snapped

def line_intersect(p1, ang1, p2, ang2):
    """Intersection of two lines given a point and angle (deg) each."""
    t1, t2 = math.radians(ang1), math.radians(ang2)
    d1 = (math.cos(t1), math.sin(t1))
    d2 = (math.cos(t2), math.sin(t2))
    denom = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(denom) < 1e-9:
        return p1  # parallel (shouldn't happen at a real corner)
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    t = (dx*d2[1] - dy*d2[0]) / denom
    return (p1[0] + d1[0]*t, p1[1] + d1[1]*t)

def regularize_letter(pts):
    n = len(pts)
    # 1) classify + snap each edge's angle
    edges = []
    for i in range(n):
        p0, p1 = pts[i], pts[(i+1) % n]
        dx, dy = p1[0]-p0[0], p1[1]-p0[1]
        raw_angle = math.degrees(math.atan2(dy, dx)) % 180
        angle = snap_angle(raw_angle)
        edges.append({"p0": p0, "p1": p1, "angle": angle})

    # 1b) merge consecutive edges that snapped to the same angle - these are
    # a single straight run the original trace split into two near-identical
    # segments (pixel/antialiasing wiggle). Two same-angle lines meeting at a
    # vertex are numerically degenerate to intersect (near-parallel -> the
    # solved point can shoot arbitrarily far away), so collapse them first.
    merged = [edges[0]]
    for e in edges[1:]:
        if merged[-1]["angle"] == e["angle"]:
            merged[-1] = {"p0": merged[-1]["p0"], "p1": e["p1"], "angle": e["angle"]}
        else:
            merged.append(e)
    if len(merged) > 1 and merged[0]["angle"] == merged[-1]["angle"]:
        merged[0] = {"p0": merged[-1]["p0"], "p1": merged[0]["p1"], "angle": merged[0]["angle"]}
        merged.pop()
    edges = merged
    n = len(edges)

    # 2) snap each edge's rail offset, clustering within each angle class
    for target_angle in (0, 45, 90, 135):
        idxs = [i for i, e in enumerate(edges) if e["angle"] == target_angle]
        offsets = [edge_offset(edges[i]["p0"], target_angle) for i in idxs]
        snapped = cluster(offsets, RAIL_CLUSTER_TOL)
        for i, off in zip(idxs, snapped):
            edges[i]["offset"] = off

    # 3) force stroke-width-range rail *pairs* within each angle class to the
    #    canonical stroke width - but only when a pair of edges on those two
    #    rails actually face each other across a stroke (their extents along
    #    the rail direction overlap), not just because the offsets happen to
    #    be numerically close somewhere unrelated in the letter.
    def along_extent(e):
        theta = math.radians(e["angle"])
        d = (math.cos(theta), math.sin(theta))
        t0 = e["p0"][0]*d[0] + e["p0"][1]*d[1]
        t1 = e["p1"][0]*d[0] + e["p1"][1]*d[1]
        return (min(t0, t1), max(t0, t1))

    def overlaps(a, b):
        return min(a[1], b[1]) - max(a[0], b[0]) > 0.15  # meaningful overlap, not just touching

    for target_angle in (0, 45, 90, 135):
        idxs = [i for i, e in enumerate(edges) if e["angle"] == target_angle]
        rails = sorted(set(edges[i]["offset"] for i in idxs))
        rail_edges = {r: [i for i in idxs if edges[i]["offset"] == r] for r in rails}
        adjust = {}
        used = set()
        for j in range(len(rails) - 1):
            r0, r1 = rails[j], rails[j+1]
            if r0 in used or r1 in used:
                continue
            gap = r1 - r0
            if not (STROKE_PAIR_MIN <= gap <= STROKE_PAIR_MAX):
                continue
            paired = any(overlaps(along_extent(edges[i]), along_extent(edges[k]))
                         for i in rail_edges[r0] for k in rail_edges[r1])
            if paired:
                adjust[r1] = r0 + CANONICAL_STROKE
                used.add(r0); used.add(r1)
        for i in idxs:
            if edges[i]["offset"] in adjust:
                edges[i]["offset"] = adjust[edges[i]["offset"]]

    # 4) re-solve each vertex as the intersection of its two neighbouring
    #    (now exact) edge lines
    new_pts = []
    for i in range(n):
        prev_e = edges[i-1]
        cur_e = edges[i]
        theta = math.radians(cur_e["angle"])
        n_ = (-math.sin(theta), math.cos(theta))
        ref_cur = (n_[0]*cur_e["offset"], n_[1]*cur_e["offset"])
        theta_p = math.radians(prev_e["angle"])
        n_p = (-math.sin(theta_p), math.cos(theta_p))
        ref_prev = (n_p[0]*prev_e["offset"], n_p[1]*prev_e["offset"])
        new_pts.append(line_intersect(ref_prev, prev_e["angle"], ref_cur, cur_e["angle"]))
    return new_pts

letters = load_letters(TRACED_SVG)
regularized = {name: regularize_letter(pts) for name, pts in letters.items()}

all_x = [p[0] for pts in regularized.values() for p in pts]
all_y = [p[1] for pts in regularized.values() for p in pts]
W = max(all_x) - min(all_x) + 2*MARGIN_MM
H = max(all_y) - min(all_y) + 2*MARGIN_MM
ox, oy = min(all_x) - MARGIN_MM, min(all_y) - MARGIN_MM

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{H:.3f}mm" viewBox="0 0 {W:.3f} {H:.3f}">']
for name, pts in regularized.items():
    d = "M " + " L ".join(f"{x-ox:.3f},{y-oy:.3f}" for x, y in pts) + " Z"
    svg.append(f'  <path id="{name}" d="{d}" fill="#000000"/>')
svg.append('</svg>')
with open(OUT_SVG, "w") as f:
    f.write("\n".join(svg) + "\n")
print(f"wrote {OUT_SVG}  ({W:.2f} x {H:.2f} mm)")
for name, pts in regularized.items():
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    print(f"  {name}: {len(pts)} vertices, w={max(xs)-min(xs):.3f}mm h={max(ys)-min(ys):.3f}mm")
