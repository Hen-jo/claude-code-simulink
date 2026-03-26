# Simulink MATLAB Bridge Skill

This repository is not a standalone service. It is a skill-style Python bridge that helps an agent work with Simulink models through MATLAB.

The core flow is intentionally simple:

- The agent produces a JSON specification
- The Python bridge renders MATLAB scripts
- MATLAB is executed mainly through `matlab -batch`
- Outputs, logs, and reports are written to files

Primary use cases:

- Build Simulink models from specifications
- Inspect existing models and summarize them for discussion
- Clone models into new files
- Run validation, compile checks, smoke tests, and test cases
- Generate code with `slbuild`

## Repository Layout

- [SKILL.md](/Users/jo/LBD/SKILL.md): skill definition
- [scripts/simulink_bridge.py](/Users/jo/LBD/scripts/simulink_bridge.py): main bridge script
- [references/spec.md](/Users/jo/LBD/references/spec.md): model JSON contract
- [references/matlab-integration.md](/Users/jo/LBD/references/matlab-integration.md): integration notes
- [examples/pid_spec.json](/Users/jo/LBD/examples/pid_spec.json): model generation example
- [examples/test_cases.json](/Users/jo/LBD/examples/test_cases.json): test case example

## Requirements

Base requirements:

- Python 3
- MATLAB
- Simulink

Additional requirements by feature:

- `codegen`: Simulink Coder or Embedded Coder environment
- `matlab-engine` mode: MATLAB Engine API for Python installed

## Python Version Compatibility

Python support depends on the MATLAB release. This matters most when using `matlab.engine`, because the Python version must be supported by that specific MATLAB release.

Official MathWorks references:

- [Versions of Python Compatible with MATLAB Products by Release](https://www.mathworks.com/support/requirements/python-compatibility.html)
- [Install MATLAB Engine API for Python](https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)
- [Configure Your System to Use Python](https://www.mathworks.com/help/matlab/matlab_external/install-supported-python-implementation.html)

Examples from the official compatibility table:

- `R2025b`, `R2025a`, `R2024b`: Python `3.9`, `3.10`, `3.11`, `3.12`
- `R2024a`, `R2023b`: Python `3.9`, `3.10`, `3.11`
- `R2023a`: Python `3.8`, `3.9`, `3.10`

The current workspace Python is `3.9.6`. That is generally compatible with many recent MATLAB releases, but you should always verify against the official compatibility table before relying on `matlab.engine`.

## Recommended Execution Strategy

The default strategy for this project is `matlab -batch`.

Why:

- MATLAB already provides an official non-interactive CLI path
- Generated `.m` scripts are easy to inspect and debug
- The agent does not need to manage long-lived MATLAB session state
- Artifacts make failures easier to reproduce

`matlab.engine` is still available as an optional mode, but it is not the default design center.

## Supported Commands

Bridge entrypoint:

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py <command> ...
```

Main commands:

- `schema`
  - Print the JSON contract summary expected from the agent
- `catalog`
  - Print the supported block catalog
- `integrations`
  - Print available MATLAB integration modes
- `build`
  - Build a `.slx` model from a JSON spec
- `inspect`
  - Read an existing model and export a JSON summary
- `clone`
  - Copy a model into a new file
- `validate`
  - Run model update and validation
- `compile`
  - Run compile / term cycles
- `smoke`
  - Run a short simulation
- `test`
  - Run JSON-defined test cases and write a report
- `codegen`
  - Run `slbuild` for code generation

## Basic Usage

### 1. Review the contract and supported blocks

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py schema
python3 /Users/jo/LBD/scripts/simulink_bridge.py catalog
python3 /Users/jo/LBD/scripts/simulink_bridge.py integrations
```

### 2. Build a model

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py build \
  --spec /Users/jo/LBD/examples/pid_spec.json \
  --output /Users/jo/LBD/PIDDemo.slx
```

You can also pipe the spec through stdin:

```bash
cat /Users/jo/LBD/examples/pid_spec.json | \
python3 /Users/jo/LBD/scripts/simulink_bridge.py build \
  --output /Users/jo/LBD/PIDDemo.slx
```

### 3. Inspect a model

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py inspect \
  --model /Users/jo/LBD/PIDDemo.slx
```

### 4. Clone a model

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py clone \
  --source /Users/jo/LBD/PIDDemo.slx \
  --output /Users/jo/LBD/PIDDemo_copy.slx
```

### 5. Validate, compile, and smoke test

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py validate --model /Users/jo/LBD/PIDDemo.slx
python3 /Users/jo/LBD/scripts/simulink_bridge.py compile --model /Users/jo/LBD/PIDDemo.slx
python3 /Users/jo/LBD/scripts/simulink_bridge.py smoke --model /Users/jo/LBD/PIDDemo.slx --stop-time 1.0
```

### 6. Run test cases

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py test \
  --model /Users/jo/LBD/PIDDemo.slx \
  --test-spec /Users/jo/LBD/examples/test_cases.json
```

### 7. Generate code

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py codegen \
  --model /Users/jo/LBD/PIDDemo.slx \
  --target ert.tlc
```

You can also use other targets such as `grt.tlc`.

## Artifacts

The bridge leaves intermediate artifacts on disk for traceability.

Examples:

- `*_artifacts/build_model.m`
- `*_artifacts/normalized_spec.json`
- `*_compile_artifacts/compile_model.m`
- `*_test_artifacts/run_tests.m`
- `*_codegen_artifacts/generate_code.m`

Why this is useful:

- You can inspect the exact MATLAB commands that were generated
- Failures are easier to reproduce
- The agent can retry based on structured outputs and saved scripts

## Dry Run

You can verify script generation even when MATLAB is not installed.

```bash
python3 /Users/jo/LBD/scripts/simulink_bridge.py build \
  --spec /Users/jo/LBD/examples/pid_spec.json \
  --output /Users/jo/LBD/PIDDemo.slx \
  --dry-run

python3 /Users/jo/LBD/scripts/simulink_bridge.py clone \
  --source /Users/jo/LBD/PIDDemo.slx \
  --output /Users/jo/LBD/PIDDemo_copy.slx \
  --dry-run

python3 /Users/jo/LBD/scripts/simulink_bridge.py test \
  --model /Users/jo/LBD/PIDDemo.slx \
  --test-spec /Users/jo/LBD/examples/test_cases.json \
  --dry-run

python3 /Users/jo/LBD/scripts/simulink_bridge.py codegen \
  --model /Users/jo/LBD/PIDDemo.slx \
  --target ert.tlc \
  --dry-run
```

## Limitations

- If `matlab` is not available on the system, execution commands will fail and only script generation will be possible
- `inspect`, `validate`, `compile`, `smoke`, `test`, and `codegen` require a real MATLAB/Simulink environment
- `codegen` depends on model configuration and available coder licenses
- `matlab.engine` has additional limitations
  - Reference: [Limitations to MATLAB Engine API for Python](https://www.mathworks.com/help/matlab/matlab_external/limitations-to-the-matlab-engine-for-python.html)

## Recommended Agent Pattern

The most practical workflow is:

1. Read `schema` and `catalog`
2. Let the agent produce a JSON spec
3. Run `build`
4. Use `inspect` when you need to discuss an existing model
5. Run `validate`, `compile`, `smoke`, and `test`
6. Finish with `codegen` if code generation is needed

In other words, the agent focuses on modeling decisions, while this bridge handles MATLAB execution and artifact management.
