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
  picks up fonts via the `~/.local/share/fonts/model-fonts-proprietary` (and,
  once it exists, `model-masks`) symlink(s) — see Fonts section) and
  headless via CLI (`inkscape in.svg --export-type=png
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

## Fonts (split across two repos — read this before adding or looking for any font)

**model-masks will go public; a sibling repo, `model-fonts`, stays private.**
Font files are split between them by license status, so no copyrighted font
software ends up in the public repo:

- **`fonts-open/`** (this repo) — fonts with a clearly open/permissive
  license (public domain, SIL OFL, explicit "free for any use including
  redistribution", etc.). Safe to be public. **Doesn't exist yet** — every
  font sourced so far turned out not to qualify (see below), so there's
  nothing to put in it. Create it (`mkdir fonts-open`) the first time a
  genuinely open-licensed font is actually added.
- **`../model-fonts/fonts-proprietary/`** (sibling repo, private, expected
  to already be cloned alongside this one at
  `/home/geoff/Projects/model-masks-workspace/model-fonts`) — everything
  else: shareware, "personal use only", "all rights reserved" with no
  redistribution grant, or no license info found at all. **When unsure,
  it goes here, not in `fonts-open/`** — that's a deliberate standing rule
  from the user, not a one-off judgment call.

**When looking for a font to use, check both directories.** When adding a
new font, check its license (embedded `name` table via fontTools — IDs 0
Copyright, 13 License, 14 LicenseURL are usually the most direct — plus a
web search if those are empty/ambiguous) and place it accordingly. See
`model-fonts/README.md` for the full rationale and a per-font license table.

Filenames are normalized to lowercase-hyphenated, derived from each font's
internal `family` metadata (via `fc-query`), not the original filename —
those varied wildly in case/spacing/relevance. Non-ASCII characters
transliterated (ü → ue). File permissions `644` (data, no execute bit).

**Resolved (2026-08-20): AmarilloUSAF font search.** The font wasn't
missing — it was in the user's Windows-partition `for_claude` folder all
along, saved under the unrelated filename `amarurgt.ttf`. Confirmed via
`fc-query` (family/fullname/postscriptname all "AmarilloUSAF") and by
diffing extracted glyph outlines byte-for-byte against a prior
browser-Claude session's pre-extracted `AmarilloUSAF_glyph_data.json`
(found in `Downloads/` on the Windows partition, now redundant). Turned out
to be registered shareware (see license table in `model-fonts/README.md`),
so it now lives in `model-fonts/fonts-proprietary/amarillo-usaf.ttf`, not
here.

**Installing fonts for local use (per machine, not git-synced):** registering
fonts with the OS font system is a per-machine step outside both repos, and
must be redone on each machine after a fresh clone/pull. Run, once
`model-fonts` is cloned as a sibling of this repo:

```
mkdir -p ~/.local/share/fonts
ln -sfn "$(pwd)/../model-fonts/fonts-proprietary" ~/.local/share/fonts/model-fonts-proprietary   # run from this repo's root
fc-cache -f ~/.local/share/fonts
```

(Add `ln -sfn "$(pwd)/fonts-open" ~/.local/share/fonts/model-masks` too, once
`fonts-open/` actually exists and has something in it.)

Verify with `fc-list | grep -iE "amarillo|blockschrift|raf_ww2|universj|usaaf|usn_stencil"`
— should list all 8 (all currently live in the proprietary/private set).
No root needed. This makes the fonts visible both to fontconfig-based
headless tooling and to Inkscape's GUI font picker (restart Inkscape if it
was already open) — registering the proprietary fonts locally like this is
fine, since it's a private, per-machine, non-distributed use; it's
committing them into the *public* repo that must be avoided. Symlinking
rather than copying means future additions to either `fonts-open/` or
`fonts-proprietary/` are picked up with just another `fc-cache -f`.

## Setup checklist for a new machine (Claude: run this at the start of a
## session if things look uninitialized — no .venv, no fonts symlink, etc.)

1. `./scripts/setup-venv.sh` — Python venv + fonttools.
2. Check `model-fonts` is cloned as a sibling repo (`../model-fonts` from
   this repo's root) — it holds the proprietary/unclear-license fonts and
   is private, so it won't come along with a public clone of this repo. If
   missing, ask the user rather than guessing a clone URL.
3. Font symlink(s) + `fc-cache -f` per the font-install steps above.
4. Inkscape — check `inkscape --version`; if missing, it needs `sudo apt
   install inkscape` (see README's software table), which needs the user to
   run it (Claude has no root — see gotcha above). Ask the user rather than
   attempting sudo.
5. Repo may have uncommitted changes carried over via git — check `git
   status` before assuming a clean tree.
