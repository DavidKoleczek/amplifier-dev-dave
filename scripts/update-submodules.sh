#!/bin/bash

# Script to pull latest changes for all Amplifier submodules
# Usage: ./update-submodules.sh

set -e

# Modules in dependency order
MODULES=(
    "amplifier-core"
    "amplifier-config"
    "amplifier-profiles"
    "amplifier-app-cli"
    "amplifier-app-benchmarks"
    "amplifier-module-context-simple"
    "amplifier-module-loop-streaming"
    "amplifier-module-tool-bash"
    "amplifier-module-tool-todo"
)

echo "Pulling latest changes for all submodules..."
echo ""

for module in "${MODULES[@]}"; do
    if [ -d "$module" ]; then
        echo "  Updating $module..."
        cd "$module"
        git checkout main
        git pull
        cd ..
    else
        echo "  [SKIP] $module (not found)"
    fi
done

echo ""
echo "All submodules updated!"
