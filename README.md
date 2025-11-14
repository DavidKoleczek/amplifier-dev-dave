# Amplifier Development Workspace

This repository contains copies of relevant Amplifier repositories as submodules for convenient development.
This repo is based on [microsoft/amplifier-dev](https://github.com/microsoft/amplifier-dev)


## Modules Copied

- [amplifier-module-provider-openai](https://github.com/microsoft/amplifier-module-provider-openai/)

## Local Development Modules

These are modules that are actively being developed.
Eventually, these may graduate to their own repos.

- **amplifier-module-provider-openai-v2** - Improved OpenAI provider following best practices (local development)

## Modules as Submodules

There are repos that are meant to be more stable and we are unlikely to need to make significant changes to them.

- [amplifier-app-cli](https://github.com/microsoft/amplifier-app-cli/)
- [amplifier-core](https://github.com/microsoft/amplifier-core/)
- [amplifier-module-context-simple](https://github.com/microsoft/amplifier-module-context-simple/)
- [amplifier-module-loop-streaming](https://github.com/microsoft/amplifier-module-loop-streaming/)
- [amplifier-config](https://github.com/microsoft/amplifier-config/tree/)
- [amplifier-profiles](https://github.com/microsoft/amplifier-profiles/tree/)

## Modules Used

These are repos that are stable, not dependencies of others, and there is a minimal chance we will need to modify them.
These are listed here for reference as they are used in amplifier profiles.

- [amplifier-collection-toolkit](https://github.com/microsoft/amplifier-collection-toolkit/)
- [amplifier-module-hooks-streaming-ui](https://github.com/microsoft/amplifier-module-hooks-streaming-ui/)
- [amplifier-module-provider-anthropic](https://github.com/microsoft/amplifier-module-provider-anthropic/)
- [amplifier-module-provider-azure-openai](https://github.com/microsoft/amplifier-module-provider-azure-openai/)
- [amplifier-module-tool-bash](https://github.com/microsoft/amplifier-module-tool-bash/)
- [amplifier-module-tool-filesystem](https://github.com/microsoft/amplifier-module-tool-filesystem/)
- [amplifier-module-tool-search](https://github.com/microsoft/amplifier-module-tool-search/)
- [amplifier-module-tool-task](https://github.com/microsoft/amplifier-module-tool-task/)
- [amplifier-module-tool-todo](https://github.com/microsoft/amplifier-module-tool-todo/)
- [amplifier-module-tool-web](https://github.com/microsoft/amplifier-module-tool-web/)
- [amplifier-module-resolution](https://github.com/microsoft/amplifier-module-resolution/tree/)


# Development

## Prerequisites

- Currently focused on development for Windows Subsystem for Linux (WSL). Other platforms may work with minor changes but are not officially supported.
- [uv](https://github.com/astral-sh/uv)


## Installation

```bash
./scripts/install-dev.sh
```


## Updating Submodules

To pull the latest changes from all submodules:

```bash
./scripts/update-submodules.sh
```


## Code Formatting

All local modules are automatically formatted with ruff after any file edits (via Claude Code PostToolUse hook).

To manually format all local modules:

```bash
./scripts/format.sh
```


## Running amplifier in CLI

```bash
amplifier run --profile dev-local "hello!"
```


## Running amplifier in the debugger

A debug configuration is at [.vscode/launch.json](.vscode/launch.json) for running the CLI in the debugger.

