#!/bin/sh
# Coblings launcher for Linux/macOS (needs Python 3.11+, nothing else).
# Messages stay ASCII-only so they render under any terminal.
# No pipefail: it is not POSIX and older /bin/sh (dash) rejects it.
set -eu

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$ROOT/src"
export PYTHONPATH

PY=""
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "[coblings] Python 3 not found. Install Python 3.11+ and try again." >&2
    exit 1
fi

# Incremental build: skips work when nothing under src/ changed.
"$PY" "$ROOT/tools/build.py"

exec "$PY" -m coblings "$@"
