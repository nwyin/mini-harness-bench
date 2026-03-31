"""Basic tests for the protocol encoder/decoder roundtrip."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import encode_message
from server import decode_message


def test_roundtrip_simple():
    """Encode then decode a simple message."""
    msg = {"type": "request", "action": "ping"}
    data = encode_message(msg)
    result = decode_message(data)
    assert result == msg


def test_roundtrip_response():
    """Encode then decode a response message."""
    msg = {"type": "response", "status": "ok"}
    data = encode_message(msg)
    result = decode_message(data)
    assert result == msg
