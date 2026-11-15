#!/usr/bin/env bash
# One-button RL run. Usage:  ./run_rl.sh [hours]      (default 8; "smoke" for a ~6 min check)
# Creates a venv, installs numpy/pandas/torch, downloads the public Metrica sample games,
# then trains + validates + writes rl/runs/latest/report.md. Safe to stop and re-run (resumes).
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
[ -d .venv_rl ] || "$PY" -m venv .venv_rl
# shellcheck disable=SC1091
source .venv_rl/bin/activate
pip install -q --upgrade pip
pip install -q -r rl/requirements.txt
if [ "${1:-8}" = "smoke" ]; then
  python -m rl.run_all --smoke
else
  python -m rl.run_all --hours "${1:-8}" 2>&1 | tee -a rl/run_console.log
fi
