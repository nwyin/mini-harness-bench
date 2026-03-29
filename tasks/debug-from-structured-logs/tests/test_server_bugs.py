"""Tests for debug-from-structured-logs task."""

import os
import sys
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
        if mod_name in ("server",):
            del sys.modules[mod_name]


def test_malformed_metadata_returns_error():
    """Malformed JSON metadata must return error, not raise exception."""
    _setup()
    try:
        from server import RequestProcessor

        proc = RequestProcessor()
        resp = proc.process_request({"type": "order", "user_id": "u1", "payload": {"items": []}, "metadata": "not-valid{{{"})
        assert resp["status"] == "error"
        assert "metadata" in resp["message"].lower() or "json" in resp["message"].lower()
    finally:
        _cleanup()


def test_malformed_metadata_empty_string():
    """Empty string metadata must also be handled gracefully."""
    _setup()
    try:
        from server import RequestProcessor

        proc = RequestProcessor()
        resp = proc.process_request({"type": "order", "user_id": "u1", "payload": {"items": []}, "metadata": ""})
        # Empty string is invalid JSON, should return error
        assert resp["status"] == "error"
    finally:
        _cleanup()


def test_precision_simple():
    """3 items at $0.10 each should total exactly $0.30."""
    _setup()
    try:
        from server import OrderCalculator

        calc = OrderCalculator()
        items = [{"price": 0.10, "quantity": 1} for _ in range(3)]
        total = calc.calculate_total(items)
        assert total == 0.30, f"Expected 0.30 but got {total}"
    finally:
        _cleanup()


def test_precision_large_order():
    """150 items at $100.00 each should total exactly $15000.00."""
    _setup()
    try:
        from server import OrderCalculator

        calc = OrderCalculator()
        items = [{"price": 100.00, "quantity": 1} for _ in range(150)]
        total = calc.calculate_total(items)
        assert total == 15000.00, f"Expected 15000.00 but got {total}"
    finally:
        _cleanup()


def test_precision_with_discount_and_tax():
    """Discount and tax calculations must also be precise."""
    _setup()
    try:
        from server import OrderCalculator

        calc = OrderCalculator()
        total = calc.calculate_total([{"price": 33.33, "quantity": 3}])
        assert total == 99.99, f"Expected 99.99 but got {total}"
        discounted = calc.apply_discount(total, 10.0)
        assert discounted == 89.99, f"Expected 89.99 but got {discounted}"
    finally:
        _cleanup()


def test_cache_atomic_update():
    """Two sequential updates to the same user must both be reflected."""
    _setup()
    try:
        from server import UserCache

        cache = UserCache()
        cache.update("u1", {"name": "Alice", "email": "alice@test.com", "preferences": {"theme": "dark"}})
        cache.update("u1", {"address": "123 Main St", "phone": "555-0100"})

        result = cache.get("u1")
        assert result is not None
        # All fields from both updates must be present
        assert result["name"] == "Alice"
        assert result["email"] == "alice@test.com"
        assert result["address"] == "123 Main St"
        assert result["phone"] == "555-0100"
    finally:
        _cleanup()


def test_cache_update_does_not_share_reference():
    """Updating cache must not allow external mutation of cached data."""
    _setup()
    try:
        from server import UserCache

        cache = UserCache()
        data = {"name": "Bob"}
        cache.update("u2", data)

        # Mutating the original dict should not affect the cache
        data["name"] = "CHANGED"
        result = cache.get("u2")
        assert result["name"] == "Bob"

        # Mutating the returned dict should not affect the cache
        result["name"] = "ALSO_CHANGED"
        result2 = cache.get("u2")
        assert result2["name"] == "Bob"
    finally:
        _cleanup()


def test_full_order_flow_with_metadata():
    """Full order request with valid metadata must work correctly."""
    _setup()
    try:
        import json

        from server import RequestProcessor

        proc = RequestProcessor()
        resp = proc.process_request(
            {
                "type": "order",
                "user_id": "u10",
                "payload": {
                    "items": [{"price": 25.00, "quantity": 4}],
                    "discount_pct": 10.0,
                    "tax_rate": 0.08,
                },
                "metadata": json.dumps({"source": "web"}),
            }
        )
        assert resp["status"] == "ok"
        assert resp["subtotal"] == 100.00
        assert resp["total"] == 97.20  # 100 - 10% = 90, + 8% tax = 97.20
    finally:
        _cleanup()
