#!/usr/bin/env python3
"""Extract simplified straight-edge letter outlines from a scanned decal
crop, using OpenCV contour detection. Prints per-letter pixel measurements
(bounding box, inter-letter gaps) so a canonical real-world scale and
letter-spacing can be chosen before generating an SVG.

Usage: trace-decal-letters.py <image> [--epsilon-frac 0.006]
"""
import sys
import argparse
import cv2
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--epsilon-frac", type=float, default=0.006,
                     help="approxPolyDP epsilon as a fraction of each contour's perimeter")
    ap.add_argument("--min-area", type=float, default=200)
    args = ap.parse_args()

    img = cv2.imread(args.image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # decal ink is near-black on a light-blue background: fixed threshold is
    # more stable here than Otsu, since the background is flat and light.
    _, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > args.min_area]
    contours.sort(key=lambda c: cv2.boundingRect(c)[0])

    letters = []
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, args.epsilon_frac * peri, True)
        x, y, w, h = cv2.boundingRect(c)
        letters.append({"points": approx.reshape(-1, 2), "bbox": (x, y, w, h)})

    print(f"{'#':>2} {'x':>6} {'y':>6} {'w':>6} {'h':>6}  vertices  gap_before")
    prev_right = None
    for i, L in enumerate(letters):
        x, y, w, h = L["bbox"]
        gap = "" if prev_right is None else f"{x - prev_right:.1f}"
        print(f"{i:>2} {x:>6} {y:>6} {w:>6} {h:>6}  {len(L['points']):>8}  {gap}")
        prev_right = x + w

    np.save("/tmp/letters_debug.npy", np.array([L["points"] for L in letters], dtype=object), allow_pickle=True)
    print(f"\n{len(letters)} letter(s) found; simplified vertex arrays saved to /tmp/letters_debug.npy")

if __name__ == "__main__":
    main()
