#!/bin/bash

# Script to add Amplifier modules as git submodules and set up development environment
# Usage: ./init.sh

set -e

GITHUB_ORG="microsoft"
DEFAULT_BRANCH="main"

# Modules in dependency order (used for both submodules and installation)
MODULES=(
    "amplifier-core"
    "amplifier-config"
    "amplifier-profiles"
    "amplifier-app-cli"
    "amplifier-module-context-simple"
    "amplifier-module-loop-streaming"
    "amplifier-module-provider-openai"
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

uv venv --python 3.11
uv pip install ruff pytest pytest-asyncio

for module in "${MODULES[@]}"; do
  echo "  Installing $module..."
  cd "$module"
  uv pip install -e . > /dev/null
  cd ..
done
