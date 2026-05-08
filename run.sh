#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
    .venv/bin/python -m textual_widgets.storybook "$@"
else
    python3 -m textual_widgets.storybook "$@"
fi
