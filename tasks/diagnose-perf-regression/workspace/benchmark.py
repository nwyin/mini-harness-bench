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
