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
