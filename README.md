# Amplifier Development Workspace

This repository contains all relevant Amplifier repositories as submodules for convenient development.
This repo is based on [microsoft/amplifier-dev](https://github.com/microsoft/amplifier-dev)


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