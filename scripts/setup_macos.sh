#!/usr/bin/env bash
set -euo pipefail

skill_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_command="${PYTHON:-python3}"

if ! command -v "$python_command" >/dev/null 2>&1; then
  echo "Python 3 is required. Install it first, then rerun this script." >&2
  exit 1
fi

"$python_command" -m venv "$skill_root/.venv"
"$skill_root/.venv/bin/python" -m pip install --upgrade pip
"$skill_root/.venv/bin/python" -m pip install -r "$skill_root/requirements.txt"
"$skill_root/.venv/bin/python" "$skill_root/scripts/rednote_video_lens.py" doctor

echo "RedNote Video Lens is ready on macOS/Linux."
