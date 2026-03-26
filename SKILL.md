---
name: simulink-matlab-bridge
description: Use when a user wants an agent-friendly workflow for creating, inspecting, cloning, compiling, validating, testing, or generating embedded code from Simulink models through Python and MATLAB. This skill provides a thin Python bridge that accepts structured model specs, emits MATLAB scripts, and mainly drives Simulink through matlab -batch.
---

# Simulink MATLAB Bridge

Use this skill when the task is to bridge an agent and Simulink, not to build a standalone CLI.

## What this skill does

- Defines the JSON contract an agent should emit for Simulink model generation
- Exposes the supported block catalog and MATLAB integration options
- Generates `.slx` models from specs
- Inspects an existing model and exports a machine-readable summary
- Clones an existing model into a new file
- Compiles a model by running update and compile/term cycles
- Runs validation, smoke simulations, and test cases with report JSON
- Generates code through `slbuild` for Embedded Coder or GRT targets
- Uses `matlab -batch` as the main execution path

## Workflow

1. Read [references/spec.md](references/spec.md) for the JSON contract.
2. If needed, read [references/matlab-integration.md](references/matlab-integration.md) for integration tradeoffs.
3. Have the agent produce a JSON spec.
4. Run one of these:

```bash
python3 scripts/simulink_bridge.py schema
python3 scripts/simulink_bridge.py catalog
python3 scripts/simulink_bridge.py integrations
python3 scripts/simulink_bridge.py build --spec examples/pid_spec.json --output PIDDemo.slx
python3 scripts/simulink_bridge.py inspect --model PIDDemo.slx
python3 scripts/simulink_bridge.py clone --source PIDDemo.slx --output PIDDemo_copy.slx
python3 scripts/simulink_bridge.py validate --model PIDDemo.slx
python3 scripts/simulink_bridge.py compile --model PIDDemo.slx
python3 scripts/simulink_bridge.py smoke --model PIDDemo.slx --stop-time 1.0
python3 scripts/simulink_bridge.py test --model PIDDemo.slx --test-spec examples/test_cases.json
python3 scripts/simulink_bridge.py codegen --model PIDDemo.slx --target ert.tlc
```

## Notes

- `build` accepts `--spec` or JSON on stdin.
- Prefer batch execution unless there is a clear reason to keep a live MATLAB Engine session.
- When validation fails, the script returns structured `issues` so the agent can repair the spec and retry.
- Keep the agent focused on spec generation and model reasoning. Let the Python bridge handle MATLAB command execution details.
