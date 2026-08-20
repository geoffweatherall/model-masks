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
