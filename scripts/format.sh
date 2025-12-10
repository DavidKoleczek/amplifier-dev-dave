#!/bin/bash

# Script to format all local modules with ruff
# Usage: ./format.sh

set -e

# Get the absolute path to the repo root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUFF_CONFIG="$REPO_ROOT/ruff.toml"
RUFF="$REPO_ROOT/.venv/bin/ruff"

# Local modules to format
LOCAL_MODULES=(
    "amplifier-app-benchmarks"
)

echo "Formatting all local modules with ruff..."
echo "Using config: $RUFF_CONFIG"
echo ""

for module in "${LOCAL_MODULES[@]}"; do
    if [ -d "$REPO_ROOT/$module" ]; then
        echo "Processing $module..."

        echo "  - Formatting..."
        "$RUFF" format --config "$RUFF_CONFIG" "$REPO_ROOT/$module"
        echo "  - Fixing lints..."
        "$RUFF" check --fix --config "$RUFF_CONFIG" "$REPO_ROOT/$module"

        echo ""
    else
        echo "[SKIP] $module (not found)"
        echo ""
    fi
done

echo "All modules formatted!"
