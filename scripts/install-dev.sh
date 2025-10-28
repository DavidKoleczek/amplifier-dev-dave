# Amplifier development environment setup script

uv venv --python 3.11

# Install dev dependencies
uv pip install ruff pytest

# Install modules in this order
MODULES=(
  "amplifier-core"
  "amplifier-app-cli"
  "amplifier-module-context-simple"
  "amplifier-module-hooks-streaming-ui"
  "amplifier-module-loop-streaming"
  "amplifier-module-provider-anthropic"
  "amplifier-module-tool-web"
)

for module in "${MODULES[@]}"; do
  echo "Installing $module..."
  cd "$module"
  uv pip install -e .
  cd ..
done
