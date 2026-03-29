"""Simple request-processing server with caching and order calculations."""

from __future__ import annotations

import json
from typing import Any


class UserCache:
    """In-memory cache for user data."""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, user_id: str) -> dict[str, Any] | None:
        return self._cache.get(user_id)

    def update(self, user_id: str, data: dict[str, Any]) -> None:
        """Update cache entry for a user.

        BUG: This does a partial update that can corrupt data when called
        concurrently for the same user_id. If two requests update different
        fields, intermediate state can be read.
        """
        existing = self._cache.get(user_id, {})
        # This non-atomic read-modify-write can interleave with another update
        for key, value in data.items():
            existing[key] = value
        self._cache[user_id] = existing

    def clear(self) -> None:
        self._cache.clear()


class OrderCalculator:
    """Calculates order totals."""

    @staticmethod
    def calculate_total(items: list[dict[str, Any]]) -> float:
        """Calculate total price for a list of order items.

        Each item has 'price' (float) and 'quantity' (int).

        BUG: Uses floating-point addition which accumulates rounding errors
        on large orders. Should use integer cents or Decimal.
        """
        total = 0.0
        for item in items:
            total += item["price"] * item["quantity"]
        return total

    @staticmethod
    def apply_discount(total: float, discount_pct: float) -> float:
        """Apply a percentage discount."""
        return total * (1.0 - discount_pct / 100.0)

    @staticmethod
    def calculate_tax(total: float, tax_rate: float) -> float:
        """Calculate tax amount."""
        return total * tax_rate


class RequestProcessor:
    """Processes incoming requests."""

    def __init__(self) -> None:
        self.cache = UserCache()
        self.calculator = OrderCalculator()

    def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process a single request and return a response.

        Request format:
        {
            "type": "order" | "profile_update" | "query",
            "user_id": "...",
            "payload": { ... },
            "metadata": "..." (optional, JSON string)
        }
        """
        req_type = request.get("type", "")
        user_id = request.get("user_id", "")
        payload = request.get("payload", {})

        # Parse metadata if present
        # BUG: No error handling for malformed JSON in metadata
        metadata = {}
        if "metadata" in request:
            metadata = json.loads(request["metadata"])

        if req_type == "order":
            return self._handle_order(user_id, payload, metadata)
        elif req_type == "profile_update":
            return self._handle_profile_update(user_id, payload)
        elif req_type == "query":
            return self._handle_query(user_id)
        else:
            return {"status": "error", "message": f"Unknown request type: {req_type}"}

    def _handle_order(self, user_id: str, payload: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
        items = payload.get("items", [])
        discount = payload.get("discount_pct", 0.0)
        tax_rate = payload.get("tax_rate", 0.0)

        subtotal = self.calculator.calculate_total(items)
        after_discount = self.calculator.apply_discount(subtotal, discount)
        tax = self.calculator.calculate_tax(after_discount, tax_rate)
        total = after_discount + tax

        # Update user's order history in cache
        cached = self.cache.get(user_id) or {}
        order_count = cached.get("order_count", 0) + 1
        self.cache.update(user_id, {"order_count": order_count, "last_total": total})

        return {
            "status": "ok",
            "subtotal": subtotal,
            "discount_applied": subtotal - after_discount,
            "tax": tax,
            "total": total,
            "order_number": order_count,
        }

    def _handle_profile_update(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.cache.update(user_id, payload)
        return {"status": "ok", "user_id": user_id, "updated_fields": list(payload.keys())}

    def _handle_query(self, user_id: str) -> dict[str, Any]:
        cached = self.cache.get(user_id)
        if cached is None:
            return {"status": "ok", "user_id": user_id, "data": None}
        return {"status": "ok", "user_id": user_id, "data": dict(cached)}

    def process_batch(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process multiple requests and return responses."""
        responses = []
        for req in requests:
            resp = self.process_request(req)
            responses.append(resp)
        return responses
