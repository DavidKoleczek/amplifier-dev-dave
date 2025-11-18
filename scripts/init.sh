#!/bin/bash

# Script to add Amplifier modules as git submodules and set up development environment
# Usage: ./init.sh

set -e

GITHUB_ORG="microsoft"
DEFAULT_BRANCH="main"

# Install submodules in this order
# NOTE: It is important that amplifier-app-cli is first, so the the next packages override its dependencies correctly (namely the amplifier-core)
MODULES=(
    "amplifier-app-cli"
    "amplifier-core"
    "amplifier-config"
    "amplifier-profiles"
    "amplifier-module-context-simple"
    "amplifier-module-provider-openai"
)

# Local modules (not submodules)
LOCAL_MODULES=(
    "amplifier-module-orchestrator-coding"
    "amplifier-module-provider-openai-v2"
    "amplifier-module-context-coding"
)

for module in "${MODULES[@]}"; do
    if git config --file .gitmodules --get "submodule.$module.path" > /dev/null 2>&1; then
        echo "  [OK] $module (already exists)"
    else
        echo "  [+] Adding $module"
        git submodule add -b "$DEFAULT_BRANCH" "https://github.com/$GITHUB_ORG/$module" "$module"
    fi
done

# Initialize and checkout main branch for submodules
# Skips those with local changes
for module in "${MODULES[@]}"; do
    if [ -d "$module" ]; then
        cd "$module"
        if git diff-index --quiet HEAD -- 2>/dev/null; then
            cd ..
            # Update submodule (init if needed)
            git submodule update --init "$module" 2>/dev/null || true
            cd "$module"
            # Ensure on main branch (not detached HEAD)
            git checkout "$DEFAULT_BRANCH" 2>/dev/null || echo "  [INFO] $module already on $DEFAULT_BRANCH"
            cd ..
        else
            echo "  [SKIP] $module (has local changes)"
            cd ..
        fi
    fi
done

uv venv --python 3.11
uv pip install ruff pytest pytest-asyncio

for module in "${MODULES[@]}"; do
  echo "  Installing $module..."
  cd "$module"
  uv pip install -e . > /dev/null
  cd ..
done

# Install local modules
for module in "${LOCAL_MODULES[@]}"; do
  if [ -d "$module" ]; then
    echo "  Installing $module..."
    cd "$module"
    uv pip install -e . > /dev/null
    cd ..
  else
    echo "  [SKIP] $module (not found)"
  fi
done
