"""In-process message transport for testing client/server communication.

Uses a simple queue to pass encoded messages between client and server
without any network I/O.
"""

from __future__ import annotations

import queue
from typing import Any

from client import encode_message
from server import decode_message


class Transport:
    """Bidirectional in-process message transport."""

    def __init__(self) -> None:
        self._outbound: queue.Queue[bytes] = queue.Queue()
        self._inbound: queue.Queue[bytes] = queue.Queue()

    def send(self, msg: dict[str, Any]) -> None:
        """Encode and enqueue a message for the server."""
        data = encode_message(msg)
        self._outbound.put(data)

    def receive(self) -> dict[str, Any]:
        """Dequeue and decode the next message from the client."""
        data = self._outbound.get(timeout=1.0)
        return decode_message(data)

    def respond(self, msg: dict[str, Any]) -> None:
        """Encode and enqueue a response for the client."""
        data = encode_message(msg)
        self._inbound.put(data)

    def get_response(self) -> dict[str, Any]:
        """Dequeue and decode the next response from the server."""
        data = self._inbound.get(timeout=1.0)
        return decode_message(data)

    def roundtrip(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Encode a message, then immediately decode it (for testing)."""
        data = encode_message(msg)
        return decode_message(data)
