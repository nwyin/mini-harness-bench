from __future__ import annotations

from pathlib import Path

import yaml


def compute_correctness(tests_passed: int, tests_total: int) -> float:
    if tests_total == 0:
        return 0.0
    return tests_passed / tests_total


def load_pricing(config_path: Path | None = None) -> dict:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "pricing.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data.get("models", {})


def compute_cost(tokens: dict | None, model: str, pricing: dict) -> float:
    if tokens is None:
        return 0.0
    model_pricing = pricing.get(model)
    if model_pricing is None:
        return 0.0
    cost = 0.0
    cost += tokens.get("input", 0) * model_pricing.get("input", 0)
    cost += tokens.get("output", 0) * model_pricing.get("output", 0)
    cost += tokens.get("cache_read", 0) * model_pricing.get("cache_read", 0)
    cost += tokens.get("cache_write", 0) * model_pricing.get("cache_write", 0)
    return cost
