#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== textual-widgets Setup ==="
echo

if [[ ! -d ".venv" ]]; then
    echo "Creating virtualenv..."
    python3 -m venv .venv
fi

# SSL fix for corporate proxies (Zscaler etc.) — pip.ini for ALL pip invocations
if [[ ! -f ".venv/pip.conf" ]]; then
    cat > .venv/pip.conf <<'EOF'
[global]
trusted-host = pypi.org pypi.python.org files.pythonhosted.org
EOF
fi

echo "Activating .venv..."
# shellcheck source=/dev/null
source .venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet

echo "Installing textual-widgets with storybook themes and dev dependencies..."
pip install -e ".[dev,storybook]"

echo
echo "=== Setup complete ==="
echo "Run the storybook with:  ./run.sh"
echo "Run tests with:          .venv/bin/pytest tests"
