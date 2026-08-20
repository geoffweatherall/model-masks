#!/usr/bin/env bash
# Sets up the project-local Python venv without needing root.
#
# On this project's Ubuntu machines, `python3 -m venv` fails because the
# `python3-venv`/ensurepip apt package isn't installed (and we don't have
# root). Workaround: create the venv anyway (it succeeds structurally, just
# without pip), then bootstrap pip into it manually via get-pip.py. No sudo
# required.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
    python3 -m venv .venv || true  # expected to warn about ensurepip; venv dir is still created
fi

if [ ! -x .venv/bin/pip ]; then
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    .venv/bin/python3 /tmp/get-pip.py
fi

.venv/bin/pip install -r requirements.txt
echo "venv ready: .venv/bin/python3"
