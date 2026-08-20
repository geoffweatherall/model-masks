# model-masks

Producing SVG cut files for a Silhouette Portrait 3, used to cut masks for
painting scale models.

## Software requirements

This table is kept current as the single source of truth for what needs to
be installed on a machine to work on this project. **Any time new software
is installed for this project, add a row here with install instructions** —
Claude has no root access (see CLAUDE.md), so anything needing `sudo` must
be run by the human; Claude will provide the exact command.

| Tool | Purpose | Install | Status |
|---|---|---|---|
| Python 3 venv (`.venv`) | Scripted SVG/font tooling (e.g. fonttools) | `./scripts/setup-venv.sh` (no root needed) | Automated |
| [fonttools](https://github.com/fonttools/fonttools) | Extract glyph outlines from `.ttf` files without needing them installed at the OS level | via `requirements.txt` / `setup-venv.sh` | Automated |
| [Inkscape](https://inkscape.org/) | SVG editing, path boolean ops, font rendering for design work | `sudo apt install inkscape` | **Installed** (2026-08-20, v1.4.3) — confirmed working both headful (normal GUI use) and headless (CLI export/actions work with no `DISPLAY` set, no Xvfb needed) |

Run `./scripts/setup-venv.sh` once per machine to set up the Python venv.

## Fonts

Font files (`.ttf`) may be checked into the repo. For scripted glyph-to-path
extraction, they're loaded directly by file path (no OS install needed). For
using them interactively in Inkscape, they need to be registered at the user
level (`~/.local/share/fonts`, then `fc-cache -f`) — no root required. Cut
files that use text should have it converted to outlined paths before being
treated as final, so the deliverable SVG has no font dependency at cut time.
