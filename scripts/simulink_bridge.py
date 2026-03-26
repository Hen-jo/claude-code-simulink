#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional


SUPPORTED_BLOCKS: Dict[str, Dict[str, Any]] = {
    "Inport": {
        "libraryPath": "simulink/Sources/In1",
        "category": "Sources",
        "description": "External model input",
        "params": [],
    },
    "Outport": {
        "libraryPath": "simulink/Sinks/Out1",
        "category": "Sinks",
        "description": "External model output",
        "params": [],
    },
    "Scope": {
        "libraryPath": "simulink/Sinks/Scope",
        "category": "Sinks",
        "description": "Visualize signals during simulation",
        "params": [],
    },
    "Gain": {
        "libraryPath": "simulink/Math Operations/Gain",
        "category": "Math Operations",
        "description": "Multiply input by a scalar gain",
        "params": ["Gain"],
    },
    "Sum": {
        "libraryPath": "simulink/Math Operations/Sum",
        "category": "Math Operations",
        "description": "Sum or subtract multiple inputs",
        "params": ["Inputs"],
    },
    "Integrator": {
        "libraryPath": "simulink/Continuous/Integrator",
        "category": "Continuous",
        "description": "Continuous-time integration",
        "params": [],
    },
    "Derivative": {
        "libraryPath": "simulink/Continuous/Derivative",
        "category": "Continuous",
        "description": "Continuous-time derivative",
        "params": [],
    },
    "TransferFcn": {
        "libraryPath": "simulink/Continuous/Transfer Fcn",
        "category": "Continuous",
        "description": "Continuous transfer function block",
        "params": ["Numerator", "Denominator"],
    },
    "Step": {
        "libraryPath": "simulink/Sources/Step",
        "category": "Sources",
        "description": "Step input source",
        "params": [],
    },
    "SineWave": {
        "libraryPath": "simulink/Sources/Sine Wave",
        "category": "Sources",
        "description": "Sine wave source",
        "params": [],
    },
    "Constant": {
        "libraryPath": "simulink/Sources/Constant",
        "category": "Sources",
        "description": "Constant source",
        "params": ["Value"],
    },
    "Switch": {
        "libraryPath": "simulink/Signal Routing/Switch",
        "category": "Signal Routing",
        "description": "Select between two signals",
        "params": [],
    },
    "Mux": {
        "libraryPath": "simulink/Signal Routing/Mux",
        "category": "Signal Routing",
        "description": "Combine signals into a vector",
        "params": ["Inputs"],
    },
    "Demux": {
        "libraryPath": "simulink/Signal Routing/Demux",
        "category": "Signal Routing",
        "description": "Split a vector signal",
        "params": ["Outputs"],
    },
    "UnitDelay": {
        "libraryPath": "simulink/Discrete/Unit Delay",
        "category": "Discrete",
        "description": "Delay signal by one sample",
        "params": [],
    },
    "ZeroOrderHold": {
        "libraryPath": "simulink/Discrete/Zero-Order Hold",
        "category": "Discrete",
        "description": "Hold input across a sample interval",
        "params": ["SampleTime"],
    },
    "LogicalOperator": {
        "libraryPath": "simulink/Logic and Bit Operations/Logical Operator",
        "category": "Logic and Bit Operations",
        "description": "Boolean operator",
        "params": ["Operator"],
    },
    "Relay": {
        "libraryPath": "simulink/Discontinuities/Relay",
        "category": "Discontinuities",
        "description": "Relay with hysteresis",
        "params": [],
    },
    "Saturation": {
        "libraryPath": "simulink/Discontinuities/Saturation",
        "category": "Discontinuities",
        "description": "Clamp a signal to limits",
        "params": ["UpperLimit", "LowerLimit"],
    },
    "LookupTable1D": {
        "libraryPath": "simulink/Lookup Tables/1-D Lookup Table",
        "category": "Lookup Tables",
        "description": "One-dimensional lookup table",
        "params": ["BreakpointsForDimension1", "Table"],
    },
}


INTEGRATIONS = [
    {
        "id": "batch",
        "recommended": True,
        "description": "Use local matlab -batch to execute rendered scripts and Simulink commands.",
    },
    {
        "id": "matlab-engine",
        "recommended": False,
        "description": "Use matlab.engine directly from Python when a long-lived session is useful.",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent-friendly Python bridge for Simulink and MATLAB")
    subparsers = parser.add_subparsers(dest="command", required=True)

    schema_parser = subparsers.add_parser("schema")
    schema_parser.add_argument("--pretty", action="store_true")

    catalog_parser = subparsers.add_parser("catalog")
    catalog_parser.add_argument("--pretty", action="store_true")

    integrations_parser = subparsers.add_parser("integrations")
    integrations_parser.add_argument("--pretty", action="store_true")

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--spec", help="Path to spec JSON. Reads stdin when omitted.")
    build_parser.add_argument("--output", required=True, help="Output .slx path")
    build_parser.add_argument("--engine", default="batch", choices=["auto", "matlab-engine", "batch"])
    build_parser.add_argument("--matlab-bin", help="Path to matlab executable")
    build_parser.add_argument("--work-dir", help="Artifact directory")
    build_parser.add_argument("--dry-run", action="store_true")

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--model", required=True, help="Path to .slx file")
    inspect_parser.add_argument("--output", help="Optional output JSON path")
    inspect_parser.add_argument("--matlab-bin", help="Path to matlab executable")

    clone_parser = subparsers.add_parser("clone")
    clone_parser.add_argument("--source", required=True, help="Source .slx model")
    clone_parser.add_argument("--output", required=True, help="Cloned .slx file")
    clone_parser.add_argument("--matlab-bin", help="Path to matlab executable")
    clone_parser.add_argument("--work-dir", help="Artifact directory")
    clone_parser.add_argument("--dry-run", action="store_true")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--model", required=True)
    validate_parser.add_argument("--engine", default="batch", choices=["auto", "matlab-engine", "batch"])
    validate_parser.add_argument("--matlab-bin", help="Path to matlab executable")
    validate_parser.add_argument("--work-dir", help="Artifact directory")

    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("--model", required=True, help="Path to .slx file")
    compile_parser.add_argument("--matlab-bin", help="Path to matlab executable")
    compile_parser.add_argument("--work-dir", help="Artifact directory")

    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("--model", required=True)
    smoke_parser.add_argument("--stop-time", default="1.0")
    smoke_parser.add_argument("--engine", default="batch", choices=["auto", "matlab-engine", "batch"])
    smoke_parser.add_argument("--matlab-bin", help="Path to matlab executable")
    smoke_parser.add_argument("--work-dir", help="Artifact directory")

    test_parser = subparsers.add_parser("test")
    test_parser.add_argument("--model", required=True, help="Path to .slx file")
    test_parser.add_argument("--test-spec", required=True, help="JSON file with test cases")
    test_parser.add_argument("--matlab-bin", help="Path to matlab executable")
    test_parser.add_argument("--work-dir", help="Artifact directory")
    test_parser.add_argument("--dry-run", action="store_true")

    codegen_parser = subparsers.add_parser("codegen")
    codegen_parser.add_argument("--model", required=True, help="Path to .slx file")
    codegen_parser.add_argument("--target", default="ert.tlc", help="System target file, for example ert.tlc or grt.tlc")
    codegen_parser.add_argument("--matlab-bin", help="Path to matlab executable")
    codegen_parser.add_argument("--work-dir", help="Artifact directory")
    codegen_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "schema":
            print_json(schema_payload(), pretty=args.pretty)
            return 0
        if args.command == "catalog":
            print_json(catalog_payload(), pretty=args.pretty)
            return 0
        if args.command == "integrations":
            print_json(integrations_payload(), pretty=args.pretty)
            return 0
        if args.command == "build":
            spec = read_spec(args.spec)
            result = handle_build(spec, args.output, args.engine, args.matlab_bin, args.work_dir, args.dry_run)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
        if args.command == "inspect":
            result = handle_inspect(args.model, args.output, args.matlab_bin)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
        if args.command == "clone":
            result = handle_clone(args.source, args.output, args.matlab_bin, args.work_dir, args.dry_run)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
        if args.command == "validate":
            result = handle_validate(args.model, args.engine, args.matlab_bin, args.work_dir)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
        if args.command == "compile":
            result = handle_compile(args.model, args.matlab_bin, args.work_dir)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
        if args.command == "smoke":
            result = handle_smoke(args.model, args.stop_time, args.engine, args.matlab_bin, args.work_dir)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
        if args.command == "test":
            result = handle_test(args.model, args.test_spec, args.matlab_bin, args.work_dir, args.dry_run)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
        if args.command == "codegen":
            result = handle_codegen(args.model, args.target, args.matlab_bin, args.work_dir, args.dry_run)
            print_json(result, pretty=True)
            return 0 if result.get("ok") else 1
    except ValidationError as exc:
        print_json({"ok": False, "kind": "validation_error", "issues": exc.issues}, pretty=True)
        return 1
    except Exception as exc:
        print_json({"ok": False, "kind": "runtime_error", "error": str(exc)}, pretty=True)
        return 1

    return 1


class ValidationError(Exception):
    def __init__(self, issues: List[Dict[str, Any]]):
        self.issues = issues
        message = issues[0]["message"] if issues else "validation error"
        super().__init__(message)


def schema_payload() -> Dict[str, Any]:
    return {
        "version": "v1",
        "description": "Agent-to-Simulink bridge contract. Generate this JSON and pass it to build.",
        "requiredTopLevelFields": ["model", "blocks", "connections", "simulation", "validation"],
        "blockTypeSource": "catalog",
        "output": "Simulink .slx file plus execution artifacts",
    }


def catalog_payload() -> Dict[str, Any]:
    blocks = []
    for block_type, meta in sorted(SUPPORTED_BLOCKS.items()):
        entry = {"type": block_type}
        entry.update(meta)
        blocks.append(entry)
    return {"version": "v1", "blocks": blocks}


def integrations_payload() -> Dict[str, Any]:
    return {
        "version": "v1",
        "recommendedMode": "batch",
        "integrations": INTEGRATIONS,
        "matlabEngineAvailable": matlab_engine_available(),
        "matlabBinaryOnPath": shutil.which("matlab") is not None,
    }


def read_spec(path: Optional[str]) -> Dict[str, Any]:
    if path:
        return json.loads(Path(path).read_text())
    raw = sys.stdin.read()
    if not raw.strip():
        raise RuntimeError("build requires --spec or JSON on stdin")
    return json.loads(raw)


def normalize_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    spec = deepcopy(spec)
    spec.setdefault("version", "v1")
    spec.setdefault("model", {})
    spec["model"].setdefault("name", "GeneratedModel")
    spec["model"].setdefault("description", "")
    spec.setdefault("blocks", [])
    spec.setdefault("connections", [])
    spec.setdefault("simulation", {})
    spec["simulation"].setdefault("stopTime", "10")
    spec["simulation"].setdefault("solver", "ode45")
    spec["simulation"].setdefault("stepSize", "")
    spec.setdefault("validation", {})
    spec["validation"].setdefault("compileCheck", True)
    spec["validation"].setdefault("smokeTest", True)
    spec["validation"].setdefault("expectedSignals", [])
    spec.setdefault("issues", [])

    for index, block in enumerate(spec["blocks"]):
        block["id"] = sanitize_id(block.get("id", f"block_{index+1}"))
        block.setdefault("params", {})
        block_type = block.get("type")
        if block_type in SUPPORTED_BLOCKS and not block.get("libraryPath"):
            block["libraryPath"] = SUPPORTED_BLOCKS[block_type]["libraryPath"]
        block.setdefault("position", [30 + index * 100, 120, 70 + index * 100, 150])

    for conn in spec["connections"]:
        conn["srcBlock"] = sanitize_id(conn.get("srcBlock", ""))
        conn["dstBlock"] = sanitize_id(conn.get("dstBlock", ""))

    spec["model"]["name"] = sanitize_id(spec["model"]["name"])
    return spec


def validate_spec(spec: Dict[str, Any]) -> None:
    issues: List[Dict[str, Any]] = []
    if not spec["model"].get("name"):
        issues.append(issue("missing_model_name", "model.name", "model.name is required"))
    if not spec["blocks"]:
        issues.append(issue("missing_blocks", "blocks", "at least one block is required"))

    block_ids = set()
    for block in spec["blocks"]:
        block_id = block.get("id")
        if not block_id:
            issues.append(issue("missing_block_id", "blocks[].id", "block.id is required"))
            continue
        if block_id in block_ids:
            issues.append(issue("duplicate_block_id", "blocks[].id", f"duplicate block id '{block_id}'"))
        block_ids.add(block_id)
        block_type = block.get("type")
        if block_type not in SUPPORTED_BLOCKS:
            issues.append(issue("unsupported_block_type", "blocks[].type", f"unsupported block type '{block_type}'"))
        if not block.get("libraryPath"):
            issues.append(issue("missing_library_path", "blocks[].libraryPath", f"block '{block_id}' is missing libraryPath"))
        position = block.get("position", [])
        if not isinstance(position, list) or len(position) != 4:
            issues.append(issue("invalid_position", "blocks[].position", f"block '{block_id}' position must have four integers"))

    for conn in spec["connections"]:
        if conn.get("srcBlock") not in block_ids:
            issues.append(issue("missing_connection_source", "connections[].srcBlock", f"connection source '{conn.get('srcBlock')}' does not exist"))
        if conn.get("dstBlock") not in block_ids:
            issues.append(issue("missing_connection_destination", "connections[].dstBlock", f"connection destination '{conn.get('dstBlock')}' does not exist"))
        if int(conn.get("srcPort", 0)) < 1 or int(conn.get("dstPort", 0)) < 1:
            issues.append(issue("invalid_port_number", "connections[].srcPort", "connection ports must be >= 1"))

    if issues:
        raise ValidationError(issues)


def handle_build(spec: Dict[str, Any], output_path: str, engine_mode: str, matlab_bin: Optional[str], work_dir: Optional[str], dry_run: bool) -> Dict[str, Any]:
    normalized = normalize_spec(spec)
    validate_spec(normalized)

    output = Path(output_path).resolve()
    artifacts_dir = Path(work_dir).resolve() if work_dir else output.parent / f"{normalized['model']['name']}_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    normalized_path = artifacts_dir / "normalized_spec.json"
    normalized_path.write_text(json.dumps(normalized, indent=2))

    report_path = artifacts_dir / "build_report.json"
    script_path = artifacts_dir / "build_model.m"
    script_path.write_text(render_build_script(normalized, output, report_path))

    result = {
        "ok": True,
        "command": "build",
        "integrationMode": resolve_engine_mode(engine_mode, matlab_bin),
        "modelName": normalized["model"]["name"],
        "outputPath": str(output),
        "normalizedSpecPath": str(normalized_path),
        "generatedScriptPath": str(script_path),
        "matlabReportPath": str(report_path),
        "issues": normalized.get("issues", []),
        "matlabInvoked": False,
    }

    if dry_run:
        return result

    execution = execute_matlab_script(script_path, engine_mode, matlab_bin)
    result["matlabInvoked"] = True
    result["execution"] = execution
    result["ok"] = execution["ok"]
    if not execution["ok"]:
        result["error"] = execution.get("error")
    return result


def handle_inspect(model_path: str, output_path: Optional[str], matlab_bin: Optional[str]) -> Dict[str, Any]:
    model = Path(model_path).resolve()
    inspection_path = Path(output_path).resolve() if output_path else model.with_suffix(".inspection.json")
    script_path = inspection_path.with_suffix(".inspect.m")
    script_path.write_text(render_inspect_script(model, inspection_path))
    execution = execute_with_batch(script_path, matlab_bin)
    return {
        "ok": execution["ok"],
        "command": "inspect",
        "integrationMode": "batch",
        "modelPath": str(model),
        "inspectionPath": str(inspection_path),
        "generatedScriptPath": str(script_path),
        "execution": execution,
        "error": execution.get("error"),
    }


def handle_clone(source_path: str, output_path: str, matlab_bin: Optional[str], work_dir: Optional[str], dry_run: bool) -> Dict[str, Any]:
    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    artifacts_dir = Path(work_dir).resolve() if work_dir else output.parent / f"{output.stem}_clone_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "clone_report.json"
    script_path = artifacts_dir / "clone_model.m"
    script_path.write_text(render_clone_script(source, output, report_path))
    result = {
        "ok": True,
        "command": "clone",
        "integrationMode": "batch",
        "sourcePath": str(source),
        "outputPath": str(output),
        "generatedScriptPath": str(script_path),
        "matlabReportPath": str(report_path),
        "matlabInvoked": False,
    }
    if dry_run:
        return result
    execution = execute_with_batch(script_path, matlab_bin)
    result["matlabInvoked"] = True
    result["execution"] = execution
    result["ok"] = execution["ok"]
    result["error"] = execution.get("error")
    return result


def handle_validate(model_path: str, engine_mode: str, matlab_bin: Optional[str], work_dir: Optional[str]) -> Dict[str, Any]:
    model = Path(model_path).resolve()
    artifacts_dir = Path(work_dir).resolve() if work_dir else model.parent / f"{model.stem}_validate_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    report_path = artifacts_dir / "validate_report.json"
    script_path = artifacts_dir / "validate_model.m"
    script_path.write_text(render_validate_script(model, report_path))

    execution = execute_matlab_script(script_path, engine_mode, matlab_bin)
    return {
        "ok": execution["ok"],
        "command": "validate",
        "integrationMode": resolve_engine_mode(engine_mode, matlab_bin),
        "modelPath": str(model),
        "generatedScriptPath": str(script_path),
        "matlabReportPath": str(report_path),
        "execution": execution,
        "error": execution.get("error"),
    }


def handle_compile(model_path: str, matlab_bin: Optional[str], work_dir: Optional[str]) -> Dict[str, Any]:
    model = Path(model_path).resolve()
    artifacts_dir = Path(work_dir).resolve() if work_dir else model.parent / f"{model.stem}_compile_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    report_path = artifacts_dir / "compile_report.json"
    script_path = artifacts_dir / "compile_model.m"
    script_path.write_text(render_compile_script(model, report_path))

    execution = execute_with_batch(script_path, matlab_bin)
    return {
        "ok": execution["ok"],
        "command": "compile",
        "integrationMode": "batch",
        "modelPath": str(model),
        "generatedScriptPath": str(script_path),
        "matlabReportPath": str(report_path),
        "execution": execution,
        "error": execution.get("error"),
    }


def handle_smoke(model_path: str, stop_time: str, engine_mode: str, matlab_bin: Optional[str], work_dir: Optional[str]) -> Dict[str, Any]:
    model = Path(model_path).resolve()
    artifacts_dir = Path(work_dir).resolve() if work_dir else model.parent / f"{model.stem}_smoke_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    report_path = artifacts_dir / "smoke_report.json"
    script_path = artifacts_dir / "smoke_model.m"
    script_path.write_text(render_smoke_script(model, stop_time, report_path))

    execution = execute_matlab_script(script_path, engine_mode, matlab_bin)
    return {
        "ok": execution["ok"],
        "command": "smoke",
        "integrationMode": resolve_engine_mode(engine_mode, matlab_bin),
        "modelPath": str(model),
        "stopTime": stop_time,
        "generatedScriptPath": str(script_path),
        "matlabReportPath": str(report_path),
        "execution": execution,
        "error": execution.get("error"),
    }


def handle_test(model_path: str, test_spec_path: str, matlab_bin: Optional[str], work_dir: Optional[str], dry_run: bool) -> Dict[str, Any]:
    model = Path(model_path).resolve()
    test_spec = json.loads(Path(test_spec_path).read_text())
    normalized = normalize_test_spec(test_spec)
    artifacts_dir = Path(work_dir).resolve() if work_dir else model.parent / f"{model.stem}_test_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    normalized_path = artifacts_dir / "normalized_test_spec.json"
    normalized_path.write_text(json.dumps(normalized, indent=2))
    report_path = artifacts_dir / "test_report.json"
    script_path = artifacts_dir / "run_tests.m"
    script_path.write_text(render_test_script(model, normalized, report_path))

    result = {
        "ok": True,
        "command": "test",
        "integrationMode": "batch",
        "modelPath": str(model),
        "testSpecPath": str(Path(test_spec_path).resolve()),
        "normalizedTestSpecPath": str(normalized_path),
        "generatedScriptPath": str(script_path),
        "matlabReportPath": str(report_path),
        "matlabInvoked": False,
    }
    if dry_run:
        return result
    execution = execute_with_batch(script_path, matlab_bin)
    result["matlabInvoked"] = True
    result["execution"] = execution
    result["ok"] = execution["ok"]
    result["error"] = execution.get("error")
    return result


def handle_codegen(model_path: str, target: str, matlab_bin: Optional[str], work_dir: Optional[str], dry_run: bool) -> Dict[str, Any]:
    model = Path(model_path).resolve()
    artifacts_dir = Path(work_dir).resolve() if work_dir else model.parent / f"{model.stem}_codegen_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    report_path = artifacts_dir / "codegen_report.json"
    script_path = artifacts_dir / "generate_code.m"
    script_path.write_text(render_codegen_script(model, target, report_path, artifacts_dir))

    result = {
        "ok": True,
        "command": "codegen",
        "integrationMode": "batch",
        "modelPath": str(model),
        "target": target,
        "generatedScriptPath": str(script_path),
        "matlabReportPath": str(report_path),
        "artifactDir": str(artifacts_dir),
        "matlabInvoked": False,
    }
    if dry_run:
        return result
    execution = execute_with_batch(script_path, matlab_bin)
    result["matlabInvoked"] = True
    result["execution"] = execution
    result["ok"] = execution["ok"]
    result["error"] = execution.get("error")
    return result


def render_build_script(spec: Dict[str, Any], output_path: Path, report_path: Path) -> str:
    model_name = matlab_escape(spec["model"]["name"])
    commands = [
        "bdclose('all');",
        f"new_system('{model_name}');",
        f"open_system('{model_name}');",
    ]

    for block in spec["blocks"]:
        block_path = f"{spec['model']['name']}/{block['id']}"
        position = "[" + " ".join(str(int(x)) for x in block["position"]) + "]"
        commands.append(
            f"add_block('{matlab_escape(block['libraryPath'])}', '{matlab_escape(block_path)}', 'Position', {position}, 'MakeNameUnique', 'off');"
        )
        if block.get("params"):
            param_parts = []
            for key, value in sorted(block["params"].items()):
                param_parts.append(f"'{matlab_escape(str(key))}'")
                param_parts.append(f"'{matlab_escape(str(value))}'")
            commands.append(f"set_param('{matlab_escape(block_path)}', {', '.join(param_parts)});")

    for conn in spec["connections"]:
        commands.append(
            f"add_line('{model_name}', '{matlab_escape(conn['srcBlock'])}/{int(conn['srcPort'])}', '{matlab_escape(conn['dstBlock'])}/{int(conn['dstPort'])}', 'autorouting', 'on');"
        )

    commands.append(f"set_param('{model_name}', 'Solver', '{matlab_escape(spec['simulation']['solver'])}');")
    commands.append(f"set_param('{model_name}', 'StopTime', '{matlab_escape(spec['simulation']['stopTime'])}');")
    if spec["simulation"].get("stepSize"):
        commands.append(f"set_param('{model_name}', 'FixedStep', '{matlab_escape(spec['simulation']['stepSize'])}');")
    commands.append(f"save_system('{model_name}', '{matlab_escape(str(output_path))}');")

    return render_matlab_wrapper(commands, report_path, stage="build", extra_fields={"model": str(output_path)})


def render_validate_script(model_path: Path, report_path: Path) -> str:
    commands = [
        "bdclose('all');",
        f"load_system('{matlab_escape(str(model_path))}');",
        f"[~, modelName, ~] = fileparts('{matlab_escape(str(model_path))}');",
        "set_param(modelName, 'SimulationCommand', 'update');",
    ]
    return render_matlab_wrapper(commands, report_path, stage="validate", extra_fields={"model": str(model_path)})


def render_compile_script(model_path: Path, report_path: Path) -> str:
    commands = [
        "bdclose('all');",
        f"load_system('{matlab_escape(str(model_path))}');",
        f"[~, modelName, ~] = fileparts('{matlab_escape(str(model_path))}');",
        "set_param(modelName, 'SimulationCommand', 'update');",
        "feval(modelName, [], [], [], 'compile');",
        "feval(modelName, [], [], [], 'term');",
    ]
    return render_matlab_wrapper(commands, report_path, stage="compile", extra_fields={"model": str(model_path)})


def render_inspect_script(model_path: Path, output_path: Path) -> str:
    escaped_model = matlab_escape(str(model_path))
    escaped_output = matlab_escape(str(output_path))
    lines = [
        "bdclose('all');",
        f"load_system('{escaped_model}');",
        f"[~, modelName, ~] = fileparts('{escaped_model}');",
        "blocks = find_system(modelName, 'Type', 'Block');",
        "lineHandles = find_system(modelName, 'FindAll', 'on', 'Type', 'line');",
        "blockInfo = cell(numel(blocks), 1);",
        "for i = 1:numel(blocks)",
        "    blockInfo{i} = struct(",
        "        'path', getfullname(blocks{i}), ...",
        "        'name', get_param(blocks{i}, 'Name'), ...",
        "        'blockType', get_param(blocks{i}, 'BlockType'));",
        "end",
        "result = struct(",
        "    'ok', true, ...",
        "    'model', modelName, ...",
        "    'solver', get_param(modelName, 'Solver'), ...",
        "    'stopTime', get_param(modelName, 'StopTime'), ...",
        "    'blockCount', numel(blocks), ...",
        "    'lineCount', numel(lineHandles), ...",
        "    'blocks', {blockInfo});",
        f"fid = fopen('{escaped_output}', 'w');",
        "fwrite(fid, jsonencode(result), 'char');",
        "fclose(fid);",
    ]
    return "\n".join(lines) + "\n"


def render_clone_script(source_path: Path, output_path: Path, report_path: Path) -> str:
    commands = [
        "bdclose('all');",
        f"load_system('{matlab_escape(str(source_path))}');",
        f"[~, modelName, ~] = fileparts('{matlab_escape(str(source_path))}');",
        f"save_system(modelName, '{matlab_escape(str(output_path))}');",
    ]
    return render_matlab_wrapper(commands, report_path, stage="clone", extra_fields={"source": str(source_path), "output": str(output_path)})


def render_smoke_script(model_path: Path, stop_time: str, report_path: Path) -> str:
    commands = [
        "bdclose('all');",
        f"load_system('{matlab_escape(str(model_path))}');",
        f"[~, modelName, ~] = fileparts('{matlab_escape(str(model_path))}');",
        f"sim(modelName, 'StopTime', '{matlab_escape(stop_time)}');",
    ]
    return render_matlab_wrapper(report_path=report_path, stage="smoke", commands=commands, extra_fields={"model": str(model_path), "stopTime": stop_time})


def render_test_script(model_path: Path, test_spec: Dict[str, Any], report_path: Path) -> str:
    cases_json = matlab_escape(json.dumps(test_spec["cases"], ensure_ascii=False))
    escaped_model = matlab_escape(str(model_path))
    escaped_report = matlab_escape(str(report_path))
    lines = [
        "bdclose('all');",
        f"load_system('{escaped_model}');",
        f"[~, modelName, ~] = fileparts('{escaped_model}');",
        f"cases = jsondecode('{cases_json}');",
        "results = cell(numel(cases), 1);",
        "overallOk = true;",
        "for i = 1:numel(cases)",
        "    caseOk = true;",
        "    caseError = '';",
        "    try",
        "        if isfield(cases(i), 'parameters')",
        "            paramNames = fieldnames(cases(i).parameters);",
        "            for j = 1:numel(paramNames)",
        "                name = paramNames{j};",
        "                value = cases(i).parameters.(name);",
        "                if ischar(value) || isstring(value)",
        "                    set_param(modelName, name, char(value));",
        "                else",
        "                    set_param(modelName, name, num2str(value));",
        "                end",
        "            end",
        "        end",
        "        stopTime = cases(i).stopTime;",
        "        if ~ischar(stopTime) && ~isstring(stopTime)",
        "            stopTime = num2str(stopTime);",
        "        end",
        "        sim(modelName, 'StopTime', char(stopTime));",
        "    catch ME",
        "        caseOk = false;",
        "        caseError = getReport(ME, 'extended', 'hyperlinks', 'off');",
        "        overallOk = false;",
        "    end",
        "    results{i} = struct('name', cases(i).name, 'ok', caseOk, 'error', caseError);",
        "end",
        "result = struct('ok', overallOk, 'stage', 'test', 'model', modelName, 'results', {results});",
        f"fid = fopen('{escaped_report}', 'w');",
        "fwrite(fid, jsonencode(result), 'char');",
        "fclose(fid);",
        "if ~result.ok",
        "    error('One or more test cases failed. See report JSON.');",
        "end",
    ]
    return "\n".join(lines) + "\n"


def render_codegen_script(model_path: Path, target: str, report_path: Path, artifact_dir: Path) -> str:
    escaped_model = matlab_escape(str(model_path))
    escaped_target = matlab_escape(target)
    escaped_artifact_dir = matlab_escape(str(artifact_dir))
    commands = [
        "bdclose('all');",
        f"load_system('{escaped_model}');",
        f"[~, modelName, ~] = fileparts('{escaped_model}');",
        f"cd('{escaped_artifact_dir}');",
        f"set_param(modelName, 'SystemTargetFile', '{escaped_target}');",
        "slbuild(modelName);",
    ]
    return render_matlab_wrapper(commands, report_path, stage="codegen", extra_fields={"model": str(model_path), "target": target, "artifactDir": str(artifact_dir)})


def render_matlab_wrapper(commands: List[str], report_path: Path, stage: str, extra_fields: Optional[Dict[str, str]] = None) -> str:
    result_fields = [f"'ok', false", f"'stage', '{matlab_escape(stage)}'"]
    for key, value in (extra_fields or {}).items():
        result_fields.append(f"'{matlab_escape(key)}', '{matlab_escape(str(value))}'")
    result_fields.append("'error', ''")

    lines = [f"result = struct({', '.join(result_fields)});", "try"]
    lines.extend([f"    {command}" for command in commands])
    lines.append("    result.ok = true;")
    lines.append("catch ME")
    lines.append("    result.error = getReport(ME, 'extended', 'hyperlinks', 'off');")
    lines.append("end")
    lines.append("")
    lines.append(f"fid = fopen('{matlab_escape(str(report_path))}', 'w');")
    lines.append("if fid ~= -1")
    lines.append("    fwrite(fid, jsonencode(result), 'char');")
    lines.append("    fclose(fid);")
    lines.append("end")
    lines.append("")
    lines.append("if ~result.ok")
    lines.append("    error(result.error);")
    lines.append("end")
    return "\n".join(lines) + "\n"


def execute_matlab_script(script_path: Path, engine_mode: str, matlab_bin: Optional[str]) -> Dict[str, Any]:
    resolved_mode = resolve_engine_mode(engine_mode, matlab_bin)
    if resolved_mode == "matlab-engine":
        return execute_with_engine(script_path)
    return execute_with_batch(script_path, matlab_bin)


def resolve_engine_mode(engine_mode: str, matlab_bin: Optional[str]) -> str:
    if engine_mode == "auto":
        return "batch"
    if engine_mode == "batch":
        return "batch"
    if engine_mode == "matlab-engine":
        return "matlab-engine"
    raise RuntimeError(f"unsupported engine mode '{engine_mode}'")


def matlab_engine_available() -> bool:
    try:
        import matlab.engine  # type: ignore
        return True
    except Exception:
        return False


def execute_with_engine(script_path: Path) -> Dict[str, Any]:
    try:
        import matlab.engine  # type: ignore
    except Exception as exc:
        return {"ok": False, "mode": "matlab-engine", "error": f"matlab.engine unavailable: {exc}"}

    try:
        engine = matlab.engine.start_matlab()
        escaped = matlab_escape(str(script_path.resolve()))
        engine.eval(f"run('{escaped}')", nargout=0)
        engine.quit()
        return {"ok": True, "mode": "matlab-engine"}
    except Exception as exc:
        return {"ok": False, "mode": "matlab-engine", "error": str(exc)}


def execute_with_batch(script_path: Path, matlab_bin: Optional[str]) -> Dict[str, Any]:
    binary = matlab_bin or shutil.which("matlab")
    if not binary:
        return {"ok": False, "mode": "batch", "error": "matlab executable not found"}

    escaped = matlab_escape(str(script_path.resolve()))
    completed = subprocess.run(
        [binary, "-batch", f"run('{escaped}')"],
        capture_output=True,
        text=True,
    )
    return {
        "ok": completed.returncode == 0,
        "mode": "batch",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "error": None if completed.returncode == 0 else (completed.stderr.strip() or completed.stdout.strip() or "matlab batch failed"),
    }


def sanitize_id(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value).strip().replace("-", "_").replace(" ", "_"))
    value = value.strip("_")
    return value or "unnamed"


def matlab_escape(value: str) -> str:
    return value.replace("'", "''")


def issue(code: str, field: str, message: str) -> Dict[str, Any]:
    return {"severity": "error", "code": code, "field": field, "message": message}


def normalize_test_spec(test_spec: Dict[str, Any]) -> Dict[str, Any]:
    normalized_cases = []
    for index, case in enumerate(test_spec.get("cases", [])):
        normalized_cases.append({
            "name": case.get("name", f"case_{index + 1}"),
            "stopTime": str(case.get("stopTime", "1.0")),
            "parameters": case.get("parameters", {}),
        })
    if not normalized_cases:
        raise ValidationError([issue("missing_test_cases", "cases", "at least one test case is required")])
    return {"cases": normalized_cases}


def print_json(payload: Dict[str, Any], pretty: bool = True) -> None:
    if pretty:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
