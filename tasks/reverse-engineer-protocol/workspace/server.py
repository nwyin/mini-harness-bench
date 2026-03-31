"""Protocol message decoder.

This module handles decoding of incoming binary messages according to an
internal protocol specification. The decode logic is the authoritative
reference for the wire format.
"""

from __future__ import annotations


def decode_message(data: bytes) -> dict:
    """Decode a binary protocol message into a dictionary.

    Returns a dict with keys 'type' and any payload fields.
    Raises ValueError on invalid messages.
    """
    if len(data) < 4:
        raise ValueError("Message too short")

    # Verify checksum: last byte is XOR of all preceding bytes
    _c = 0
    for _b in data[:-1]:
        _c ^= _b
    if _c != data[-1]:
        raise ValueError(f"Checksum mismatch: expected {_c:#04x}, got {data[-1]:#04x}")

    # Parse header
    _n = int.from_bytes(data[0:2], byteorder="little")
    if _n != len(data):
        raise ValueError(f"Length mismatch: header says {_n}, got {len(data)}")

    _t = data[2]
    _type_map = {1: "request", 2: "response", 3: "error"}
    if _t not in _type_map:
        raise ValueError(f"Unknown message type: {_t}")

    result: dict = {"type": _type_map[_t]}

    # Parse payload fields
    _p = 3
    _end = len(data) - 1  # exclude checksum byte
    while _p < _end:
        if _p >= _end:
            break
        _kl = data[_p]
        _p += 1
        if _p + _kl > _end:
            raise ValueError("Truncated key")
        _k = data[_p : _p + _kl].decode("utf-8")
        _p += _kl
        if _p + 2 > _end:
            raise ValueError("Truncated value length")
        _vl = int.from_bytes(data[_p : _p + 2], byteorder="little")
        _p += 2
        if _p + _vl > _end:
            raise ValueError("Truncated value")
        _v = data[_p : _p + _vl].decode("utf-8")
        _p += _vl
        result[_k] = _v

    return result
