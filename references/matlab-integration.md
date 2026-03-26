# MATLAB Integration

This skill supports two practical execution modes:

- `batch`
  - Launch local MATLAB with `matlab -batch`
- `auto`
  - Currently resolves to `batch` in this skill
- `matlab-engine`
  - Use `matlab.engine` directly from Python

Recommended default: `batch`

Why:

- MATLAB already supports non-interactive CLI execution well
- The bridge can lean on rendered `.m` scripts plus `matlab -batch`
- This keeps the implementation simple and makes behavior easier to debug from generated artifacts

This is also a good fit for:

- model compile checks
- `slbuild`-based code generation
- test execution and JSON report export

Use `integrations` to inspect the supported modes at runtime.
