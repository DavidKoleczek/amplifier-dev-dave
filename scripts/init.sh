#!/bin/bash

# Script to add Amplifier modules as git submodules and set up development environment
# Usage: ./init.sh

set -e

GITHUB_ORG="microsoft"
DEFAULT_BRANCH="main"

# Submodules in dependency order
MODULES=(
    "amplifier-core"
    "amplifier-config"
    "amplifier-profiles"
    "amplifier-app-cli"
    "amplifier-module-context-simple"
    "amplifier-module-loop-streaming"
    "amplifier-module-provider-openai"
)

# Local modules (not submodules)
LOCAL_MODULES=(
    "amplifier-module-provider-openai-v2"
)

for module in "${MODULES[@]}"; do
    if git config --file .gitmodules --get "submodule.$module.path" > /dev/null 2>&1; then
        echo "  [OK] $module (already exists)"
    else
        echo "  [+] Adding $module"
        git submodule add -b "$DEFAULT_BRANCH" "https://github.com/$GITHUB_ORG/$module" "$module"
    fi
done

git submodule update --init --recursive

# Checkout main branch for each submodule (instead of detached HEAD)
for module in "${MODULES[@]}"; do
    if [ -d "$module" ]; then
        echo "  Checking out $DEFAULT_BRANCH for $module..."
        cd "$module"
        git checkout "$DEFAULT_BRANCH"
        cd ..
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
