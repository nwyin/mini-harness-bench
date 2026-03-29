from mhb.scoring import compute_correctness, compute_cost, load_pricing


def test_correctness_perfect():
    assert compute_correctness(5, 5) == 1.0


def test_correctness_partial():
    assert compute_correctness(3, 4) == 0.75


def test_correctness_zero():
    assert compute_correctness(0, 5) == 0.0


def test_correctness_no_tests():
    assert compute_correctness(0, 0) == 0.0


def test_load_pricing():
    pricing = load_pricing()
    assert "claude-sonnet-4-20250514" in pricing
    assert "gpt-4o" in pricing
    assert pricing["claude-sonnet-4-20250514"]["input"] > 0


def test_compute_cost_basic():
    pricing = load_pricing()
    tokens = {"input": 1000, "output": 500, "cache_read": 0, "cache_write": 0}
    cost = compute_cost(tokens, "claude-sonnet-4-20250514", pricing)
    expected = 1000 * 0.000003 + 500 * 0.000015
    assert abs(cost - expected) < 1e-10


def test_compute_cost_no_tokens():
    pricing = load_pricing()
    assert compute_cost(None, "claude-sonnet-4-20250514", pricing) == 0.0


def test_compute_cost_unknown_model():
    pricing = load_pricing()
    tokens = {"input": 1000, "output": 500}
    assert compute_cost(tokens, "unknown-model", pricing) == 0.0
