"""Tests for diagnose-perf-regression task."""

from __future__ import annotations

import ast
import os
import random
import sys
import time
from pathlib import Path


def _workspace():
    pp = os.environ.get("PYTHONPATH")
    if pp:
        return Path(pp)
    return Path(__file__).resolve().parent.parent / "workspace"


def _setup():
    ws = str(_workspace())
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup():
    for mod_name in list(sys.modules):
        if mod_name in ("engine", "benchmark"):
            del sys.modules[mod_name]


NUM_CATEGORIES = 4000
CATEGORIES = [f"cat_{i:05d}" for i in range(NUM_CATEGORIES)]
TAGS = [f"tag_{i}" for i in range(20)]


def _generate_data(n: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    data = []
    for i in range(n):
        data.append(
            {
                "id": f"rec_{i:07d}",
                "category": rng.choice(CATEGORIES),
                "value": round(rng.uniform(0, 1000), 2),
                "tags": rng.sample(TAGS, k=rng.randint(0, 3)),
                "metadata": {"source": rng.choice(["api", "import", "manual"])},
            }
        )
    return data


def test_benchmark_fast():
    """process_batch on 100K items must complete in under 1.0 seconds."""
    _setup()
    try:
        from engine import process_batch

        data = _generate_data(100_000)
        allowed = CATEGORIES[: NUM_CATEGORIES // 2]

        start = time.perf_counter()
        process_batch(data, allowed, min_value=100.0)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"process_batch took {elapsed:.3f}s, expected <1.0s"
    finally:
        _cleanup()


def test_filter_uses_dict_or_set():
    """filter_records must use a set or dict for category lookup, not a linear scan."""
    _setup()
    try:
        ws = _workspace()
        source = (ws / "engine.py").read_text()
        tree = ast.parse(source)

        # Find the filter_records function
        filter_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "filter_records":
                filter_func = node
                break

        assert filter_func is not None, "filter_records function not found"

        # Check that there's no `any(... == cat for cat in allowed_categories)` pattern
        # which indicates O(n) linear scan per record
        func_source = ast.get_source_segment(source, filter_func)
        assert func_source is not None

        # The code should NOT contain a linear scan pattern like:
        #   any(record.category == cat for cat in allowed_categories)
        # It SHOULD contain set() or a direct `in` check on a set/dict
        has_linear_scan = False
        for node in ast.walk(filter_func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "any":
                    # Check if it's iterating over allowed_categories
                    for gen_node in ast.walk(node):
                        if isinstance(gen_node, ast.GeneratorExp):
                            for comp in gen_node.generators:
                                if isinstance(comp.iter, ast.Name) and comp.iter.id == "allowed_categories":
                                    has_linear_scan = True

        assert not has_linear_scan, (
            "filter_records still uses linear scan (any(... for cat in allowed_categories)). Use a set for O(1) category lookups."
        )
    finally:
        _cleanup()


def test_aggregate_bug_still_fixed():
    """The running average in aggregate_results must use (i+1) for all elements,
    not (i+1 if i>0 else 1) which was the original bug."""
    _setup()
    try:
        from engine import Record, aggregate_results

        # With the bug (i+1 if i>0 else 1), the first value gets weight 1/1,
        # second gets weight (v-avg)/2, etc. But the first value's contribution
        # is correct only with proper (i+1) = 1.
        # The bug manifests when values differ: [10, 20] should give running_avg=15
        # With the bug: step0: avg = 0 + (10-0)/1 = 10; step1: avg = 10 + (20-10)/2 = 15
        # That happens to be the same. Use [10, 20, 30]:
        # Correct: step0: 10/1=10, step1: 10+(20-10)/2=15, step2: 15+(30-15)/3=20 -> 20.0
        # Bug: step0: 0+(10-0)/1=10, step1: 10+(20-10)/2=15, step2: 15+(30-15)/3=20 -> 20.0
        # Same again. Need to check the code directly for the pattern.

        ws = _workspace()
        source = (ws / "engine.py").read_text()

        # The buggy pattern is: (i + 1 if i > 0 else 1) or equivalent
        # The fixed pattern is: (i + 1)
        # Look for the bug pattern in aggregate_results
        assert "if i > 0 else 1" not in source, (
            "aggregate_results still contains the off-by-one bug pattern: '(i + 1 if i > 0 else 1)'. Should be '(i + 1)'."
        )
        assert "if i > 0 else" not in source, (
            "aggregate_results still contains the off-by-one conditional. Should use '(i + 1)' unconditionally."
        )

        # Also verify the function works correctly
        records = [
            Record(id="1", category="A", value=10.0),
            Record(id="2", category="A", value=20.0),
            Record(id="3", category="A", value=30.0),
        ]
        results = aggregate_results(records)
        assert len(results) == 1
        assert results[0].running_avg == 20.0, f"Expected running_avg=20.0, got {results[0].running_avg}"
    finally:
        _cleanup()


def test_export_still_works():
    """export_results function must still exist and work."""
    _setup()
    try:
        from engine import AggregateResult, export_results

        aggs = [
            AggregateResult(category="alpha", count=5, total=100.0, mean=20.0, running_avg=19.5),
            AggregateResult(category="beta", count=3, total=60.0, mean=20.0, running_avg=20.1),
        ]

        csv_out = export_results(aggs, "csv")
        assert "alpha" in csv_out
        assert "beta" in csv_out
        lines = csv_out.strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows
        assert "category" in lines[0]

        md_out = export_results(aggs, "markdown")
        assert "| alpha |" in md_out or "| alpha " in md_out
        assert "|--" in md_out

        tsv_out = export_results(aggs, "tsv")
        assert "\t" in tsv_out
    finally:
        _cleanup()


def test_correctness():
    """process_batch must produce correct output (right counts, right filtering)."""
    _setup()
    try:
        from engine import process_batch

        data = [
            {"id": "1", "category": "A", "value": 50.0, "tags": ["x"]},
            {"id": "2", "category": "B", "value": 150.0, "tags": ["x", "y"]},
            {"id": "3", "category": "A", "value": 200.0, "tags": ["y"]},
            {"id": "4", "category": "C", "value": 300.0, "tags": ["x"]},
            {"id": "5", "category": "A", "value": 100.0, "tags": ["x", "y"]},
            {"id": "5", "category": "A", "value": 100.0, "tags": ["x", "y"]},  # duplicate
        ]

        result = process_batch(data, allowed_categories=["A", "B"], min_value=100.0)
        assert result["total_parsed"] == 5  # 6 raw, 1 duplicate removed
        assert result["total_filtered"] == 3  # id=2 (B,150), id=3 (A,200), id=5 (A,100)
        assert len(result["aggregates"]) == 2  # A and B

        # With required tags
        result2 = process_batch(data, allowed_categories=["A", "B"], min_value=0.0, required_tags=["x", "y"])
        # id=2 (B, tags=[x,y]), id=5 (A, tags=[x,y]) pass; id=1 (A, tags=[x]) fails y; id=3 (A, tags=[y]) fails x
        assert result2["total_filtered"] == 2
    finally:
        _cleanup()
