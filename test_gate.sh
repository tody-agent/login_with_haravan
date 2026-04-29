#!/usr/bin/env bash
set -e

echo "=== 🚀 RUNNING FULL TEST GATE ==="

# 1. Repo Safety
echo ">> [1/3] Checking Repo Safety..."
BAD_FILES=(".env" ".dev.vars" ".env.local" "site_config.json")
for file in "${BAD_FILES[@]}"; do
    if git ls-files | grep -q "$file"; then
        echo "❌ FATAL: Secret file $file is tracked by git!"
        exit 1
    fi
done
echo "✅ Git tracking looks safe."

# 2. Linting
if command -v pre-commit &> /dev/null && [ -f ".pre-commit-config.yaml" ]; then
    echo ">> [2/3] Running Lint Gate (pre-commit)..."
    pre-commit run --all-files
    echo "✅ Lint Gate passed."
else
    echo ">> [2/3] (Skipping pre-commit since it is not configured)"
fi

# 3. Python Tests Gate
echo ">> [3/3] Running Test Gate Layers (Security, Logic, API, Frontend Safety)..."
if ! python3 -c "import requests" >/dev/null 2>&1; then
    python3 -m pip install -r requirements.txt
fi
export PYTHONPATH=.
python3 -m unittest discover -s login_with_haravan/tests -v
echo "✅ Python Tests passed."

echo "=== 🎉 ALL GATES PASSED. SAFE TO DEPLOY. ==="
