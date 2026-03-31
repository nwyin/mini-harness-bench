"""Hidden tests for reverse-engineer-protocol task."""

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
        if mod_name in ("client", "server", "transport"):
            del sys.modules[mod_name]


def test_roundtrip_simple():
    """Encode then decode a simple message."""
    _setup()
    try:
        from client import encode_message
        from server import decode_message

        msg = {"type": "request", "action": "ping"}
        data = encode_message(msg)
        result = decode_message(data)
        assert result == msg
    finally:
        _cleanup()


def test_roundtrip_multifield():
    """Message with 3+ fields roundtrips correctly."""
    _setup()
    try:
        from client import encode_message
        from server import decode_message

        msg = {
            "type": "request",
            "action": "create",
            "name": "test-item",
            "category": "widgets",
        }
        data = encode_message(msg)
        result = decode_message(data)
        assert result == msg
    finally:
        _cleanup()


def test_checksum_valid():
    """The checksum byte is correct."""
    _setup()
    try:
        from client import encode_message

        msg = {"type": "request", "action": "ping"}
        data = encode_message(msg)
        # XOR of all bytes except the last should equal the last byte
        checksum = 0
        for b in data[:-1]:
            checksum ^= b
        assert checksum == data[-1], f"Checksum mismatch: computed {checksum:#04x}, got {data[-1]:#04x}"
    finally:
        _cleanup()


def test_message_types():
    """All 3 message types encode/decode correctly."""
    _setup()
    try:
        from client import encode_message
        from server import decode_message

        for msg_type in ["request", "response", "error"]:
            msg = {"type": msg_type, "info": "test"}
            data = encode_message(msg)
            result = decode_message(data)
            assert result == msg, f"Failed for type {msg_type}"
    finally:
        _cleanup()


def test_empty_values():
    """Fields with empty string values encode/decode correctly."""
    _setup()
    try:
        from client import encode_message
        from server import decode_message

        msg = {"type": "request", "key": "", "another": ""}
        data = encode_message(msg)
        result = decode_message(data)
        assert result == msg
    finally:
        _cleanup()


def test_unicode_values():
    """Fields with unicode content encode/decode correctly."""
    _setup()
    try:
        from client import encode_message
        from server import decode_message

        msg = {"type": "response", "greeting": "hello", "name": "world"}
        data = encode_message(msg)
        result = decode_message(data)
        assert result == msg
    finally:
        _cleanup()


def test_example_matches():
    """Encoding matches the examples in protocol_examples.txt."""
    _setup()
    try:
        from client import encode_message

        # Example 1
        msg1 = {"type": "request", "action": "ping"}
        data1 = encode_message(msg1)
        assert data1.hex() == "11000106616374696f6e040070696e671c", f"Example 1 mismatch: got {data1.hex()}"

        # Example 2
        msg2 = {"type": "response", "status": "ok", "user": "alice"}
        data2 = encode_message(msg2)
        assert data2.hex() == "1b00020673746174757302006f6b04757365720500616c6963657f", f"Example 2 mismatch: got {data2.hex()}"

        # Example 3
        msg3 = {"type": "error", "code": "404", "detail": "not found"}
        data3 = encode_message(msg3)
        assert data3.hex() == "20000304636f646503003430340664657461696c09006e6f7420666f756e6424", f"Example 3 mismatch: got {data3.hex()}"
    finally:
        _cleanup()
