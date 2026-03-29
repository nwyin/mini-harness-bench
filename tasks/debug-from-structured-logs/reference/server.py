"""Simple request-processing server with caching and order calculations."""

from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


class UserCache:
    """In-memory cache for user data."""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, user_id: str) -> dict[str, Any] | None:
        entry = self._cache.get(user_id)
        if entry is not None:
            return dict(entry)
        return None

    def update(self, user_id: str, data: dict[str, Any]) -> None:
        """Update cache entry for a user atomically.

        FIX: Replace entire entry with a new merged dict in a single assignment
        so no intermediate partial state can be observed.
        """
        existing = dict(self._cache.get(user_id, {}))
        merged = {**existing, **data}
        self._cache[user_id] = merged

    def clear(self) -> None:
        self._cache.clear()


class OrderCalculator:
    """Calculates order totals."""

    @staticmethod
    def calculate_total(items: list[dict[str, Any]]) -> float:
        """Calculate total price for a list of order items.

        FIX: Use Decimal for accumulation to avoid floating-point rounding errors.
        """
        total = Decimal("0")
        for item in items:
            price = Decimal(str(item["price"]))
            quantity = item["quantity"]
            total += price * quantity
        return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def apply_discount(total: float, discount_pct: float) -> float:
        """Apply a percentage discount."""
        result = Decimal(str(total)) * (1 - Decimal(str(discount_pct)) / 100)
        return float(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_tax(total: float, tax_rate: float) -> float:
        """Calculate tax amount."""
        result = Decimal(str(total)) * Decimal(str(tax_rate))
        return float(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class RequestProcessor:
    """Processes incoming requests."""

    def __init__(self) -> None:
        self.cache = UserCache()
        self.calculator = OrderCalculator()

    def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process a single request and return a response."""
        req_type = request.get("type", "")
        user_id = request.get("user_id", "")
        payload = request.get("payload", {})

        # Parse metadata if present, with error handling
        metadata = {}
        if "metadata" in request:
            try:
                metadata = json.loads(request["metadata"])
            except (json.JSONDecodeError, TypeError):
                return {"status": "error", "message": "Invalid metadata: malformed JSON"}

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
        total = float((Decimal(str(after_discount)) + Decimal(str(tax))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        # Update user's order history in cache
        cached = self.cache.get(user_id) or {}
        order_count = cached.get("order_count", 0) + 1
        self.cache.update(user_id, {"order_count": order_count, "last_total": total})

        return {
            "status": "ok",
            "subtotal": subtotal,
            "discount_applied": float(
                (Decimal(str(subtotal)) - Decimal(str(after_discount))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ),
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
        return {"status": "ok", "user_id": user_id, "data": cached}

    def process_batch(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process multiple requests and return responses."""
        responses = []
        for req in requests:
            resp = self.process_request(req)
            responses.append(resp)
        return responses
