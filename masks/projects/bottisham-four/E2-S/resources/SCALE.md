# Decal scan — scale calibration

Source: a photo scan of the Tamiya 61040 (1/48 P-51D Mustang 8th AF) kit
decal sheet, shot with a ruler alongside for scale reference. The ruler
itself has been cropped out of the stored images below — this file records
the calibration derived from it instead, so it isn't lost.

## Calibration

**606 px = 1 inch (25.4 mm) → 23.858 px/mm**, at the scan's native pixel
resolution.

Derived by locating the 1", 2", and 3" tick marks on the ruler (isolated by
thresholding for near-black ink against the ruler's dark-grey body, since
the two are close in brightness) and measuring the intervals between them:
1"→2" = 605.5 px, 2"→3" = 606.5 px. The two independent measurements agree
to within 1 px, so 606 px/inch is a solid figure.

This conversion applies unchanged to every image in this folder — none of
them have been resampled, only cropped (and, for the full sheet, re-encoded
to JPEG at quality 92 with no resizing). To size something traced from any
of these images: measure it in pixels, divide by 23.858 for mm, or by 606
for inches.

## Files and provenance

Crop offsets below are given relative to the original full-resolution scan
(4937×4032 px) as it existed before the ruler was cropped out, so they're
reproducible from the original if it's ever needed again.

| File | Crop (from original 4937×4032 scan) | Contents |
|---|---|---|
| `decal-e2-s-code.png` | 830×850 @ (1550, 0) | Fuselage code letters "E2" and "S" — decal items ③ and ④ (both duplicate rows as printed on the sheet). |
| `decal-tail-serial-413926.png` | 620×400 @ (1480, 1260) | Tail serial "413926" — decal item 24 (both duplicate rows). |

The full-sheet crop (ruler removed, 4287×4032 @ (650, 0) in the original)
was kept here briefly but has been deleted — the user has other copies of
the full scan. If more items are needed from it later, re-crop from that
copy; the offsets above (and the calibration below) still apply unchanged
since nothing here was resampled.

## Why

E2-S (44-13926) has no distinctive nose art or nickname, so its only unique
markings are the fuselage code and tail serial above — these are the pieces
worth tracing precisely for mask work.

## Tail serial: a second, independent calibration

For the tail serial tracing work, the user physically remeasured a specific
span on the actual model/reference rather than relying on the ruler-in-shot
calibration above: **left edge of "4" to right edge of "6" = 18.8mm
(given/canonical)**. In `decal-tail-serial-413926.png`'s own pixel space
that span measures 453px, giving **24.0957 px/mm** for this specific crop.

This is ~1% different from the 23.858 px/mm derived from the ruler photo
above — both crops come from the same underlying scan, so in principle they
should agree exactly; the ~1% gap is ordinary measurement tolerance (ruler
reading vs. calipers/digital measurement on the physical model). Per the
user's instruction, the freshly-given physical measurement is treated as
canonical for whatever it was given for — so all three tail-serial SVGs
below use 24.0957 px/mm, not the ruler-derived figure. Don't assume the two
figures are interchangeable across files in this folder; check which
calibration a given SVG was actually built from (recorded in this file).

## Tail serial: hand-built regularization attempt (abandoned)

First attempt at cleaning up `tail-serial-413926-traced.svg` (potrace) was
two hand-built alternatives: Approach A (every digit's centerline
hand-designed from scratch - lines and curves - then buffered to an exact
constant stroke width via `shapely`) and Approach B (a targeted hybrid,
swapping in Approach A's geometry only for "4" and "3", the two digits with
confirmed defects, keeping the rest as dense OpenCV traces of the scan).

**User feedback: both were a poor match, worse than the original trace.**
Abandoned rather than iterated further. Deleted along with their build
scripts (`build_digit_*.py`, `build_serial_approach_{a,b}.py`,
`regularize_serial_lib.py`) - don't recreate this approach for future
digit/letter regularization without a good reason; hand-designing font-like
curves from visual judgement alone did not work well here.

## Tail serial: built from usaaf-serial-stencil.ttf (current approach)

**`tail-serial-413926-font.svg`** — the font `usaaf-serial-stencil.ttf`
(now in the private `model-fonts` sibling repo's `fonts-proprietary/` -
"free for personal use" only, not clearly open, see `model-masks/CLAUDE.md`)
already has clean, correctly-designed stencil digits (constant stroke
width, proper gaps, by construction) - using it directly was a far better
result than hand-building geometry. Reuses the calibration and sizing already
established: canonical height 4.07mm (calculated, same as the traced.svg),
24.0957 px/mm, per-digit widths matching the scan (aspect-corrected per
digit, same method as the E2/S fuselage-code work), and the measured 1.37mm
inter-digit gap. Script: `scripts/build_serial_from_font.py`.

Note for reuse: font glyphs with disconnected pieces or counters (e.g. "3",
"9", "6") emit **multiple subpaths** (separate `M...Z` segments) per glyph -
treating a glyph's path data as one continuous polygon (as an earlier
version of this script did, and as `scripts/generate-e2-s-svgs.py` did
before it, for the "S" bug) puts a spurious line across the shape. Split on
each `M` into its own subpath and emit them as separate `M...Z` runs within
the same `<path d="...">` - relies on the font's own subpath winding
direction for holes to render correctly via the default nonzero fill-rule.

