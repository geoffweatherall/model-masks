# CLAUDE.md

Notes for Claude working in this repo. Content here is at Claude's discretion —
project context, conventions, and decisions worth remembering across sessions
and across machines (this repo is git-synced between two of the user's machines).

## Documentation split

- **CLAUDE.md** (this file): Claude-maintained. Working notes, conventions,
  decisions, and context that help future sessions pick up work correctly.
  Not primarily written for human reading, though humans can read it.
- **README.md** and other topic-specific markdown files: human-readable
  project documentation, written for people. Claude should read these for
  context too, but they are not where Claude records its own notes.

## Project

Producing SVG files for a Silhouette Portrait 3 cutter, used to cut masks for
painting scale models.

## Why Claude Code (not browser Claude)

Working in Claude Code rather than claude.ai's browser sandbox specifically so
that locally-installed software (e.g. Inkscape for path/boolean-ops/font-to-path
work) and system fonts are available to Claude via the Bash tool. Browser
Claude's sandbox is a fixed pre-built container — installed packages/fonts
don't persist or become available to it. Claude Code shells out directly on
the user's real machine, so anything installed there (apt packages, fonts via
`fc-cache`) is usable immediately.

## Environment gotchas (both machines are Ubuntu, similar versions)

- **No root access for Claude.** `sudo` requires interactive password auth,
  which Claude's Bash tool can't provide. Anything needing `sudo apt install`
  must be installed manually by the user — see README's software table.
  Don't keep re-attempting sudo; just tell the user the exact command to
  run. **Whenever new software gets installed for this project (by either
  of us), add/update its row in README's software table** — that table is
  the source of truth for what a fresh machine needs, and Claude should
  proactively suggest tools that would help (better Python, useful CLI
  utilities, etc.) rather than waiting to be asked.
- **Inkscape** (installed 2026-08-20, v1.4.3) works both headful (normal GUI,
  picks up fonts via the `~/.local/share/fonts/model-masks` symlink — see
  Fonts section) and headless via CLI (`inkscape in.svg --export-type=png
  --export-filename=out.png`, or `--actions=...` for scripted path ops) —
  confirmed working even with `DISPLAY`/`WAYLAND_DISPLAY` unset, no Xvfb
  needed.
- **System Python has no `ensurepip`/`pip3`, and is a PEP 668
  externally-managed-environment** — `python3 -m venv` reports failure and
  `pip install --user` is refused. Workaround (no root needed): create the
  venv anyway (the directory structure is created even though the command
  reports an ensurepip error), then bootstrap pip into it manually via
  `get-pip.py`. This is encoded in `scripts/setup-venv.sh` — use that rather
  than rediscovering the trick.
- Project Python deps go in `requirements.txt`, installed into `.venv`
  (gitignored, per-machine, recreate via the setup script rather than syncing).
- The Windows partition is dual-boot on this machine and mounts automatically
  at `/run/media/geoff/9A8832FE8832D909` when booted into Linux (NTFS,
  read-write). Useful for pulling reference material/fonts across.

## Fonts

`fonts/` at repo root holds `.ttf` files sourced from the user's Windows
partition (`for_claude` folder at `/run/media/geoff/9A8832FE8832D909/for_claude`
when dual-booted into Linux — see gotcha below). Filenames are normalized to
lowercase-hyphenated, derived from each font's internal `family` metadata
(via `fc-query`), not the original on-disk filename — those varied wildly in
case/spacing/relevance. Non-ASCII characters transliterated (ü → ue). File
permissions are `644` (data files, no execute bit needed). Current set:

| Filename | Internal family | Notes |
|---|---|---|
| `amarillo-usaf.ttf` | AmarilloUSAF | Resolved 2026-08-20 — see below |
| `blockschrift-fuer-flugzeuge.ttf` | Blockschrift für Flugzeuge | |
| `raf-ww2-851ath.ttf` | RAF_WW2_851ATH | |
| `raf-ww2-851ath-gimp.ttf` | RAF_WW2_851ATH_GIMP | |
| `universj.ttf` | UniversJ | |
| `usaaf-code-buzz.ttf` | USAAF code | "buzz" kept from original filename — common name for this USAAF buzz-number font |
| `usaaf-serial-stencil.ttf` | USAAF_Serial_Stencil | |
| `usaaf-stencil.ttf` | USAAF_Stencil | |
| `usn-stencil.ttf` | USN_Stencil | |

**Resolved (2026-08-20): AmarilloUSAF font search.** The font was not
missing — it was already present in `for_claude` all along, saved under the
unrelated filename `amarurgt.ttf` (likely the foundry's original distribution
filename; foundry tag `TLnt`). Confirmed by: (1) `fc-query` showing
family/fullname/postscriptname all reading "AmarilloUSAF", and (2) extracting
glyph outlines with fontTools and diffing them byte-for-byte against
`AmarilloUSAF_glyph_data.json` (pre-extracted by a prior browser-Claude
session, found in `Downloads/` on the Windows partition) — exact match on
path data and advance widths for every glyph checked. Copied into this repo
as `fonts/amarillo-usaf.ttf`. The glyph-data JSON/txt files on the Windows
partition are now redundant (the actual font file supersedes them) but
haven't been deleted from there — user's call if they want to clean those up.

**Installing fonts for local use (per machine, not git-synced):** the
`fonts/` directory itself is git-tracked, but registering it with the OS font
system is a per-machine step that lives outside the repo, so it must be
redone on each machine after a fresh clone/pull. Run:

```
mkdir -p ~/.local/share/fonts
ln -sfn "$(pwd)/fonts" ~/.local/share/fonts/model-masks   # run from repo root
fc-cache -f ~/.local/share/fonts
```

Verify with `fc-list | grep -iE "amarillo|blockschrift|raf_ww2|universj|usaaf|usn_stencil"`
— should list all 9. No root needed. This makes the fonts visible both to
fontconfig-based headless tooling and to Inkscape's GUI font picker (restart
Inkscape if it was already open). Symlinking rather than copying means
future additions to `fonts/` are picked up with just another `fc-cache -f`,
no re-copying.

## Setup checklist for a new machine (Claude: run this at the start of a
## session if things look uninitialized — no .venv, no fonts symlink, etc.)

1. `./scripts/setup-venv.sh` — Python venv + fonttools.
2. Font symlink + `fc-cache -f` per the font-install steps above.
3. Inkscape — check `inkscape --version`; if missing, it needs `sudo apt
   install inkscape` (see README's software table), which needs the user to
   run it (Claude has no root — see gotcha above). Ask the user rather than
   attempting sudo.
4. Repo may have uncommitted changes carried over via git — check `git
   status` before assuming a clean tree.
