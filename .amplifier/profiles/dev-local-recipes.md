---
profile:
  name: dev-local-recipes
  version: 1.0.0
  description: Local development profile with recipe execution capabilities
  extends: developer-expertise:profiles/dev.md

session:
  orchestrator:
    config:
      default_provider: provider-anthropic

providers:
  - module: provider-anthropic
    source: ./amplifier-module-provider-anthropic
    config:
      default_model: claude-sonnet-4-5
      priority: 100
  - module: provider-openai
    source: ./amplifier-module-provider-openai
    config:
      priority: 200

tools:
  - module: tool-bash
    source: ./amplifier-module-tool-bash
  - module: tool-todo
    source: ./amplifier-module-tool-todo
  - module: tool-recipes
    source: ./amplifier-collection-recipes/modules/tool-recipes
    config:
      session_dir: ~/.amplifier/projects
      auto_cleanup_days: 7

---

# Recipe Development Profile

You have access to the `tool-recipes` module for executing multi-step AI agent workflows.

## Tool Operations

### recipes(operation="execute")
Execute a recipe from YAML file.
- `recipe_path` (string, required): Path to recipe YAML file
- `context` (object, optional): Context variables for recipe execution

### recipes(operation="validate")
Validate a recipe YAML file for correctness.
- `recipe_path` (string, required): Path to recipe YAML file

### recipes(operation="resume")
Resume an interrupted recipe session.
- `session_id` (string, required): Session identifier

### recipes(operation="list")
List active recipe sessions.

### recipes(operation="approvals")
List pending approvals across sessions.

### recipes(operation="approve") / recipes(operation="deny")
Approve or deny a stage in a staged recipe.
