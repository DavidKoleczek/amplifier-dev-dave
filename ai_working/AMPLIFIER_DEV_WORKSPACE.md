# Amplifier Development Workspace

This repository contains all Amplifier repositories as submodules for convenient development.

## Repository Structure

```
amplifier-dev/
├── amplifier/          # Main Amplifier repo (currently on `next` branch)
├── amplifier-app-cli/  # `amplifier` CLI app
├── amplifier-core/     # Ultra-thin core
├── amplifier-module-*  # Reference implementations of modules
└── scripts/            # Development utilities
```

## Prerequisites

- **Python 3.11+**
- **[UV](https://github.com/astral-sh/uv)** - Fast Python package manager

### Installing UV

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quick Start

**For users** (just want to use Amplifier):

```bash
# Try without installing
uvx --from git+https://github.com/microsoft/amplifier@next amplifier

# Or install globally
uv tool install git+https://github.com/microsoft/amplifier@next
amplifier init  # First-time setup
```

**For contributors** (developing Amplifier itself):

```bash
# 1. Clone with submodules
git clone --recursive https://github.com/microsoft/amplifier-dev
cd amplifier-dev

# 2. Install UV (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install all modules in editable mode
./scripts/install-dev.sh    # macOS/Linux/WSL
# OR
.\scripts\install-dev.ps1   # Windows PowerShell

# 4. Activate virtual environment
source ../.venv/bin/activate    # macOS/Linux/WSL
# OR
..\.venv\Scripts\Activate.ps1   # Windows PowerShell

# 5. Run first-time setup
amplifier init

# 6. Run smoke test
amplifier run "What is simplicity?"
```

**Note**: The `amplifier/` submodule tracks the `next` branch. All others track `main`. See [SUBMODULE_WORKFLOW.md](./SUBMODULE_WORKFLOW.md) for details.

## Documentation

- [docs](./docs) - Core documentation and guides
  - [COLLECTIONS_GUIDE.md](./docs/COLLECTIONS_GUIDE.md) - Collections system for sharing expertise
  - [SCENARIO_TOOLS_GUIDE.md](./docs/SCENARIO_TOOLS_GUIDE.md) - Building sophisticated CLI tools
- [amplifier-core/docs](./amplifier-core/docs) - Core developer docs
- [amplifier-app-cli/docs](./amplifier-app-cli/docs) - CLI app docs

## Development Workflow

### Daily Development

```bash
# Update all submodules to latest
git submodule sync && git submodule update --init --remote --merge

# Make changes in a submodule
cd amplifier-core
# ... edit, commit ...
git push origin main  # Push immediately!
cd ..

# Update main repo to reference new commit
git add .
git commit -m "Update submodule refs"
git push origin main
```

### Running Amplifier

```bash
# Set your preferred profile (optional, persists)
amplifier profile use dev

# Run with active profile
amplifier run "Your prompt"

# Or override with --profile flag
amplifier run --profile full "Your prompt"
```

**Important**: Always push submodule commits before pushing the main repo. See [SUBMODULE_WORKFLOW.md](./SUBMODULE_WORKFLOW.md) for safe workflow patterns and verification commands.

## Testing

Run all tests:

```bash
uv run pytest
```

Run specific module tests:

```bash
cd amplifier-module-loop-basic
uv run pytest
```

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.