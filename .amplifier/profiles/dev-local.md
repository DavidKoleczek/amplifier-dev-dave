---
profile:
  name: dev-local
  version: 1.0.0
  description: Local development with available modules
  extends: foundation:profiles/base.md

session:
  orchestrator:
    module: loop-streaming
    source: file://./amplifier-module-loop-streaming
    config:
      extended_thinking: true
  context:
    module: context-simple
    source: file://./amplifier-module-context-simple

providers:
  - module: provider-anthropic
    source: file://./amplifier-module-provider-anthropic
    config:
      default_model: claude-sonnet-4-5-20250929
      debug: true

task:
  max_recursion_depth: 1

ui:
  show_thinking_stream: true
  show_tool_lines: 5

tools:
  - module: tool-web
    source: file://./amplifier-module-tool-web

hooks:
  - module: hooks-streaming-ui
    source: file://./amplifier-module-hooks-streaming-ui

agents:
  dirs:
    - ./agents
---

@foundation:context/shared/common-agent-base.md

Local development configuration with available modules. Web tools enabled, using local editable installs for development.
