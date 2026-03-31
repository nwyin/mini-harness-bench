#!/bin/bash
set -e

# The harness already did git init + committed workspace files as "initial".
# We need to rewrite history to have 3 meaningful commits.
# Strategy: reset to before initial, create our 3 commits.

git config user.email "dev@example.com"
git config user.name "Developer"

# Reset to empty state
git rm -rf . --quiet
git commit -m "remove initial" --allow-empty --quiet

# Write the benchmark file (same across all commits)
write_benchmark() {
cat > benchmark.py << 'PYEOF'
"""Benchmark script to measure process_batch performance.

Expected: <0.5s for 100K items with 4000 categories.
Current: >2s — there is a performance regression.
"""

from __future__ import annotations

import random
import time

from engine import process_batch

NUM_CATEGORIES = 4000
CATEGORIES = [f"cat_{i:05d}" for i in range(NUM_CATEGORIES)]
TAGS = [f"tag_{i}" for i in range(20)]


def generate_data(n: int, seed: int = 42) -> list[dict]:
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


def main():
    print("Generating 100,000 records...")
    data = generate_data(100_000)
    allowed = CATEGORIES[: NUM_CATEGORIES // 2]  # Half the categories

    print("Running process_batch...")
    start = time.perf_counter()
    result = process_batch(data, allowed, min_value=100.0)
    elapsed = time.perf_counter() - start

    print(f"Processed in {elapsed:.3f}s")
    print(f"  Parsed: {result['total_parsed']}")
    print(f"  Filtered: {result['total_filtered']}")
    print(f"  Aggregates: {len(result['aggregates'])}")
    print(f"  Top records: {len(result['top_records'])}")

    if elapsed > 1.0:
        print(f"\nWARNING: Processing took {elapsed:.3f}s — expected <0.5s")
        print("There appears to be a performance regression.")
    else:
        print("\nPerformance looks good.")


if __name__ == "__main__":
    main()
PYEOF
}

# --- Commit 1: Original working version ---
cat > engine.py << 'PYEOF'
"""Data processing engine for batch record operations."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class Record:
    id: str
    category: str
    value: float
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AggregateResult:
    category: str
    count: int
    total: float
    mean: float
    running_avg: float


def parse_records(raw_data: list[dict]) -> list[Record]:
    """Parse raw dictionaries into Record objects."""
    records = []
    for item in raw_data:
        record = Record(
            id=item["id"],
            category=item["category"],
            value=float(item["value"]),
            tags=item.get("tags", []),
            metadata=item.get("metadata", {}),
        )
        records.append(record)
    return records


def filter_records(
    records: list[Record],
    allowed_categories: list[str],
    min_value: float = 0.0,
    required_tags: list[str] | None = None,
) -> list[Record]:
    """Filter records by category, minimum value, and required tags.

    Only records whose category is in allowed_categories, whose value
    is >= min_value, and who have all required_tags are returned.
    """
    allowed_set = set(allowed_categories)
    result = []
    for record in records:
        if record.category not in allowed_set:
            continue
        if record.value < min_value:
            continue
        if required_tags:
            has_all = True
            for tag in required_tags:
                if tag not in record.tags:
                    has_all = False
                    break
            if not has_all:
                continue
        result.append(record)
    return result


def aggregate_results(records: list[Record]) -> list[AggregateResult]:
    """Aggregate records by category, computing count, total, mean, and running average."""
    by_category: dict[str, list[float]] = {}
    for record in records:
        by_category.setdefault(record.category, []).append(record.value)

    results = []
    for category, values in sorted(by_category.items()):
        count = len(values)
        total = sum(values)
        mean = total / count if count else 0.0

        # BUG: off-by-one in running average (uses i instead of i+1)
        running_avg = 0.0
        for i, v in enumerate(values):
            running_avg = running_avg + (v - running_avg) / (i + 1 if i > 0 else 1)

        results.append(
            AggregateResult(
                category=category,
                count=count,
                total=round(total, 6),
                mean=round(mean, 6),
                running_avg=round(running_avg, 6),
            )
        )
    return results


def rank_records(records: list[Record], top_n: int = 10) -> list[Record]:
    """Return the top N records by value, descending."""
    return sorted(records, key=lambda r: r.value, reverse=True)[:top_n]


def deduplicate(records: list[Record]) -> list[Record]:
    """Remove duplicate records (by id), keeping the first occurrence."""
    seen: set[str] = set()
    result = []
    for record in records:
        if record.id not in seen:
            seen.add(record.id)
            result.append(record)
    return result


def compute_percentiles(records: list[Record], percentiles: list[int]) -> dict[int, float]:
    """Compute value percentiles for a list of records."""
    if not records:
        return {p: 0.0 for p in percentiles}
    values = [r.value for r in records]
    result = {}
    for p in percentiles:
        result[p] = round(statistics.quantiles(values, n=100)[p - 1] if len(values) >= 2 else values[0], 6)
    return result


def process_batch(
    raw_data: list[dict],
    allowed_categories: list[str],
    min_value: float = 0.0,
    required_tags: list[str] | None = None,
    top_n: int = 10,
) -> dict:
    """Full batch processing pipeline: parse, filter, deduplicate, aggregate, rank."""
    records = parse_records(raw_data)
    records = deduplicate(records)
    filtered = filter_records(records, allowed_categories, min_value, required_tags)
    aggregates = aggregate_results(filtered)
    top = rank_records(filtered, top_n)
    return {
        "total_parsed": len(records),
        "total_filtered": len(filtered),
        "aggregates": aggregates,
        "top_records": top,
    }
PYEOF

write_benchmark
git add -A
git commit -m "Initial data processing engine with batch pipeline" --quiet

# --- Commit 2: Performance regression + legitimate bug fix ---
# Replace filter_records to use list scan instead of set, AND fix aggregate bug
cat > engine.py << 'PYEOF'
"""Data processing engine for batch record operations."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class Record:
    id: str
    category: str
    value: float
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AggregateResult:
    category: str
    count: int
    total: float
    mean: float
    running_avg: float


def parse_records(raw_data: list[dict]) -> list[Record]:
    """Parse raw dictionaries into Record objects."""
    records = []
    for item in raw_data:
        record = Record(
            id=item["id"],
            category=item["category"],
            value=float(item["value"]),
            tags=item.get("tags", []),
            metadata=item.get("metadata", {}),
        )
        records.append(record)
    return records


def filter_records(
    records: list[Record],
    allowed_categories: list[str],
    min_value: float = 0.0,
    required_tags: list[str] | None = None,
) -> list[Record]:
    """Filter records by category, minimum value, and required tags.

    Only records whose category is in allowed_categories, whose value
    is >= min_value, and who have all required_tags are returned.
    """
    result = []
    for record in records:
        # Check category membership
        if not any(record.category == cat for cat in allowed_categories):
            continue
        # Check minimum value
        if record.value < min_value:
            continue
        # Check required tags
        if required_tags:
            has_all = True
            for tag in required_tags:
                if tag not in record.tags:
                    has_all = False
                    break
            if not has_all:
                continue
        result.append(record)
    return result


def aggregate_results(records: list[Record]) -> list[AggregateResult]:
    """Aggregate records by category, computing count, total, mean, and running average."""
    by_category: dict[str, list[float]] = {}
    for record in records:
        by_category.setdefault(record.category, []).append(record.value)

    results = []
    for category, values in sorted(by_category.items()):
        count = len(values)
        total = sum(values)
        mean = total / count if count else 0.0

        # Compute running average (incrementally, as if values arrived one at a time)
        running_avg = 0.0
        for i, v in enumerate(values):
            running_avg = running_avg + (v - running_avg) / (i + 1)

        results.append(
            AggregateResult(
                category=category,
                count=count,
                total=round(total, 6),
                mean=round(mean, 6),
                running_avg=round(running_avg, 6),
            )
        )
    return results


def rank_records(records: list[Record], top_n: int = 10) -> list[Record]:
    """Return the top N records by value, descending."""
    return sorted(records, key=lambda r: r.value, reverse=True)[:top_n]


def deduplicate(records: list[Record]) -> list[Record]:
    """Remove duplicate records (by id), keeping the first occurrence."""
    seen: set[str] = set()
    result = []
    for record in records:
        if record.id not in seen:
            seen.add(record.id)
            result.append(record)
    return result


def compute_percentiles(records: list[Record], percentiles: list[int]) -> dict[int, float]:
    """Compute value percentiles for a list of records."""
    if not records:
        return {p: 0.0 for p in percentiles}
    values = [r.value for r in records]
    result = {}
    for p in percentiles:
        result[p] = round(statistics.quantiles(values, n=100)[p - 1] if len(values) >= 2 else values[0], 6)
    return result


def process_batch(
    raw_data: list[dict],
    allowed_categories: list[str],
    min_value: float = 0.0,
    required_tags: list[str] | None = None,
    top_n: int = 10,
) -> dict:
    """Full batch processing pipeline: parse, filter, deduplicate, aggregate, rank."""
    records = parse_records(raw_data)
    records = deduplicate(records)
    filtered = filter_records(records, allowed_categories, min_value, required_tags)
    aggregates = aggregate_results(filtered)
    top = rank_records(filtered, top_n)
    return {
        "total_parsed": len(records),
        "total_filtered": len(filtered),
        "aggregates": aggregates,
        "top_records": top,
    }
PYEOF

git add -A
git commit -m "Fix off-by-one in aggregate running average calculation

The running average was incorrectly using (i+1 if i>0 else 1) which skips
the proper divisor for the first element. Changed to always use (i+1).
Also cleaned up filter_records category check for readability." --quiet

# --- Commit 3: Add export_results function ---
cat > engine.py << 'PYEOF'
"""Data processing engine for batch record operations."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class Record:
    id: str
    category: str
    value: float
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AggregateResult:
    category: str
    count: int
    total: float
    mean: float
    running_avg: float


def parse_records(raw_data: list[dict]) -> list[Record]:
    """Parse raw dictionaries into Record objects."""
    records = []
    for item in raw_data:
        record = Record(
            id=item["id"],
            category=item["category"],
            value=float(item["value"]),
            tags=item.get("tags", []),
            metadata=item.get("metadata", {}),
        )
        records.append(record)
    return records


def filter_records(
    records: list[Record],
    allowed_categories: list[str],
    min_value: float = 0.0,
    required_tags: list[str] | None = None,
) -> list[Record]:
    """Filter records by category, minimum value, and required tags.

    Only records whose category is in allowed_categories, whose value
    is >= min_value, and who have all required_tags are returned.
    """
    result = []
    for record in records:
        # Check category membership
        if not any(record.category == cat for cat in allowed_categories):
            continue
        # Check minimum value
        if record.value < min_value:
            continue
        # Check required tags
        if required_tags:
            has_all = True
            for tag in required_tags:
                if tag not in record.tags:
                    has_all = False
                    break
            if not has_all:
                continue
        result.append(record)
    return result


def aggregate_results(records: list[Record]) -> list[AggregateResult]:
    """Aggregate records by category, computing count, total, mean, and running average."""
    by_category: dict[str, list[float]] = {}
    for record in records:
        by_category.setdefault(record.category, []).append(record.value)

    results = []
    for category, values in sorted(by_category.items()):
        count = len(values)
        total = sum(values)
        mean = total / count if count else 0.0

        # Compute running average (incrementally, as if values arrived one at a time)
        running_avg = 0.0
        for i, v in enumerate(values):
            running_avg = running_avg + (v - running_avg) / (i + 1)

        results.append(
            AggregateResult(
                category=category,
                count=count,
                total=round(total, 6),
                mean=round(mean, 6),
                running_avg=round(running_avg, 6),
            )
        )
    return results


def rank_records(records: list[Record], top_n: int = 10) -> list[Record]:
    """Return the top N records by value, descending."""
    return sorted(records, key=lambda r: r.value, reverse=True)[:top_n]


def deduplicate(records: list[Record]) -> list[Record]:
    """Remove duplicate records (by id), keeping the first occurrence."""
    seen: set[str] = set()
    result = []
    for record in records:
        if record.id not in seen:
            seen.add(record.id)
            result.append(record)
    return result


def compute_percentiles(records: list[Record], percentiles: list[int]) -> dict[int, float]:
    """Compute value percentiles for a list of records."""
    if not records:
        return {p: 0.0 for p in percentiles}
    values = [r.value for r in records]
    result = {}
    for p in percentiles:
        result[p] = round(statistics.quantiles(values, n=100)[p - 1] if len(values) >= 2 else values[0], 6)
    return result


def export_results(aggregates: list[AggregateResult], fmt: str = "csv") -> str:
    """Export aggregate results to a string in the given format.

    Supported formats: csv, tsv, markdown
    """
    if fmt == "csv":
        sep = ","
    elif fmt == "tsv":
        sep = "\t"
    elif fmt == "markdown":
        header = "| Category | Count | Total | Mean | Running Avg |"
        divider = "|----------|-------|-------|------|-------------|"
        rows = [f"| {a.category} | {a.count} | {a.total} | {a.mean} | {a.running_avg} |" for a in aggregates]
        return "\n".join([header, divider, *rows])
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    lines = [sep.join(["category", "count", "total", "mean", "running_avg"])]
    for agg in aggregates:
        lines.append(sep.join([agg.category, str(agg.count), str(agg.total), str(agg.mean), str(agg.running_avg)]))
    return "\n".join(lines)


def process_batch(
    raw_data: list[dict],
    allowed_categories: list[str],
    min_value: float = 0.0,
    required_tags: list[str] | None = None,
    top_n: int = 10,
) -> dict:
    """Full batch processing pipeline: parse, filter, deduplicate, aggregate, rank."""
    records = parse_records(raw_data)
    records = deduplicate(records)
    filtered = filter_records(records, allowed_categories, min_value, required_tags)
    aggregates = aggregate_results(filtered)
    top = rank_records(filtered, top_n)
    return {
        "total_parsed": len(records),
        "total_filtered": len(filtered),
        "aggregates": aggregates,
        "top_records": top,
    }
PYEOF

git add -A
git commit -m "Add export_results function for CSV, TSV, and Markdown output" --quiet
