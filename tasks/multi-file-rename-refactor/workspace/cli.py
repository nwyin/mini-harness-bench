"""Command-line interface for running DataProcessor pipelines."""

from __future__ import annotations

import json
from typing import Any

from processor import DataProcessor
from registry import clear_registry, register_processor
from runner import execute

from config import create_custom, create_from_preset, lowercase_keys, remove_nulls


def parse_args(argv: list[str]) -> dict[str, Any]:
    """Parse command-line arguments for the DataProcessor CLI.

    Supported flags:
        --name NAME        Name for the DataProcessor (required)
        --preset PRESET    Use a preset configuration
        --strict           Enable strict mode on the DataProcessor
        --input FILE       Path to input JSON file
        --output FILE      Path to output JSON file
    """
    args: dict[str, Any] = {"strict": False}
    i = 0
    while i < len(argv):
        if argv[i] == "--name" and i + 1 < len(argv):
            args["name"] = argv[i + 1]
            i += 2
        elif argv[i] == "--preset" and i + 1 < len(argv):
            args["preset"] = argv[i + 1]
            i += 2
        elif argv[i] == "--strict":
            args["strict"] = True
            i += 1
        elif argv[i] == "--input" and i + 1 < len(argv):
            args["input"] = argv[i + 1]
            i += 2
        elif argv[i] == "--output" and i + 1 < len(argv):
            args["output"] = argv[i + 1]
            i += 2
        else:
            i += 1
    return args


def build_processor(args: dict[str, Any]) -> DataProcessor:
    """Build a DataProcessor from parsed CLI arguments.

    Uses preset if specified, otherwise creates a custom DataProcessor with
    default steps (lowercase_keys, remove_nulls).
    """
    if "preset" in args:
        return create_from_preset(args["preset"])

    name = args.get("name", "cli-processor")
    proc = create_custom(
        name=name,
        steps=[lowercase_keys, remove_nulls],
        strict=args.get("strict", False),
    )
    return proc


def run_cli(argv: list[str]) -> dict[str, Any]:
    """Main CLI entry point for the DataProcessor.

    Parses arguments, builds a DataProcessor, optionally loads input data,
    runs the DataProcessor, and returns the result summary.
    """
    args = parse_args(argv)
    processor = build_processor(args)
    register_processor(processor)

    data: list[dict[str, Any]] = []
    if "input" in args:
        with open(args["input"]) as f:
            data = json.load(f)

    result = execute(processor, data)

    if "output" in args:
        with open(args["output"], "w") as f:
            json.dump(result.summary(), f, indent=2)

    clear_registry()
    return result.summary()
