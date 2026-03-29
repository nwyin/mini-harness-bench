"""Minimal routing framework for the API."""

from __future__ import annotations

import json
import re
from typing import Any, Callable


class Request:
    """Represents an incoming HTTP request."""

    def __init__(self, method: str, path: str, query: dict[str, str] | None = None, body: Any = None) -> None:
        self.method = method.upper()
        self.path = path
        self.query = query or {}
        self.body = body


class Response:
    """Represents an HTTP response."""

    def __init__(self, status: int, body: Any) -> None:
        self.status = status
        self.body = body

    def json(self) -> str:
        return json.dumps(self.body)


RouteHandler = Callable[[Request, dict[str, str]], Response]


class Router:
    """Simple pattern-matching router."""

    def __init__(self) -> None:
        self._routes: list[tuple[str, str, RouteHandler]] = []

    def add_route(self, method: str, pattern: str, handler: RouteHandler) -> None:
        """Register a route. Pattern uses {name} for path parameters."""
        self._routes.append((method.upper(), pattern, handler))

    def get(self, pattern: str) -> Callable[[RouteHandler], RouteHandler]:
        """Decorator for GET routes."""

        def decorator(fn: RouteHandler) -> RouteHandler:
            self.add_route("GET", pattern, fn)
            return fn

        return decorator

    def dispatch(self, request: Request) -> Response:
        """Find and call the matching route handler."""
        for method, pattern, handler in self._routes:
            if method != request.method:
                continue
            match = self._match_pattern(pattern, request.path)
            if match is not None:
                return handler(request, match)
        return Response(404, {"error": "not_found"})

    @staticmethod
    def _match_pattern(pattern: str, path: str) -> dict[str, str] | None:
        """Match a URL pattern against a path, extracting path parameters."""
        regex = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pattern)
        regex = f"^{regex}$"
        m = re.match(regex, path)
        if m:
            return m.groupdict()
        return None
