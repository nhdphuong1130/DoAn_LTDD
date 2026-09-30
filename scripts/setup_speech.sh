#!/usr/bin/env bash
set -euo pipefail
if [[ $# -gt 1 || ($# -eq 1 && $1 != --deps-only) ]]; then
  echo "Usage: $0 [--deps-only]" >&2
  exit 2
fi
cd "$(dirname "$0")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/speech/.cache/uv}"
if [[ ! -x speech/.venv/bin/python ]]; then
  uv venv --python 3.12 speech/.venv
fi
uv pip install --python speech/.venv/bin/python -r speech/requirements.txt
if [[ ${1:-} != --deps-only ]]; then
  speech/.venv/bin/python -m speech.setup_models
fi
