# Amplifier Development Workspace

This repository contains copies of relevant Amplifier repositories as submodules for convenient development.
This repo is based on [microsoft/amplifier-dev](https://github.com/microsoft/amplifier-dev)


## Modules Copied

- [amplifier-module-provider-openai](https://github.com/microsoft/amplifier-module-provider-openai/)

## Modules as Submodules

- [amplifier](https://github.com/microsoft/amplifier/tree/f3ff1c7ececac8757d9cbc7599e8da0f9f0f2681)
- [amplifier-app-cli](https://github.com/microsoft/amplifier-app-cli/)
- [amplifier-core](https://github.com/microsoft/amplifier-core/)
- [amplifier-module-context-simple](https://github.com/microsoft/amplifier-module-context-simple/)
- [amplifier-module-loop-streaming](https://github.com/microsoft/amplifier-module-loop-streaming/)

## Modules Used

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

- Currently focused on development for Windows Subsystem for Linux (WSL). Other platforms may work but are not officially supported.
- [uv](https://github.com/astral-sh/uv)


## Adding new git submodules (corresponding to an Amplifier module in a separate repository)

```bash
git submodule add -b <branch_name> <https_git_url> <repo_name>
```

## Updating submodules to the latest commit on their tracked branch

```bash
git submodule update --remote --merge
```

## Initializing all submodules

This is *not* required after adding a new submodule, but when cloning the repo for the first time or if submodules add their own submodules.

```bash
git submodule update --init --recursive
```

## Running amplifier in CLI

```bash
amplifier run --profile dev-local "hello!"
```
