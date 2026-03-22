#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../.."

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r env/ubuntu/requirements.txt
pip install -e .

echo ""
echo "[OK] Virtual environment is ready."
echo "[OK] Project installed in editable mode."
echo "Activate with: source .venv/bin/activate"
