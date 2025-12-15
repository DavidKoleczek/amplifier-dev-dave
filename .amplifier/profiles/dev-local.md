---
profile:
  name: dev-local
  version: 2.0.0
  description: Local development profile extending dev with Anthropic provider
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
---

# Local Development Overrides

Use local module sources for tool-bash and tool-todo for development.
