"""Protocol message encoder.

This module should encode outgoing messages into the binary protocol format
that the server's decode_message() understands. Study server.py and
protocol_examples.txt to understand the wire format.
"""

from __future__ import annotations


def encode_message(msg: dict) -> bytes:
    """Encode a dictionary into a binary protocol message.

    The input dict must have a 'type' key with value 'request', 'response',
    or 'error'. All other keys are treated as payload fields whose values
    must be strings.

    Returns the encoded bytes.
    """
    type_map = {"request": 1, "response": 2, "error": 3}
    msg_type = msg["type"]
    if msg_type not in type_map:
        raise ValueError(f"Unknown message type: {msg_type}")

    # Build payload bytes
    payload = bytearray()
    for key, value in msg.items():
        if key == "type":
            continue
        key_bytes = key.encode("utf-8")
        value_bytes = value.encode("utf-8")
        payload.append(len(key_bytes))
        payload.extend(key_bytes)
        payload.extend(len(value_bytes).to_bytes(2, byteorder="little"))
        payload.extend(value_bytes)

    # Header: 2-byte length (little-endian) + 1-byte type
    # Total length = 2 (length) + 1 (type) + len(payload) + 1 (checksum)
    total_length = 2 + 1 + len(payload) + 1
    header = total_length.to_bytes(2, byteorder="little")
    type_byte = bytes([type_map[msg_type]])

    # Assemble everything except checksum
    body = bytearray(header) + bytearray(type_byte) + payload

    # XOR checksum of all preceding bytes
    checksum = 0
    for b in body:
        checksum ^= b
    body.append(checksum)

    return bytes(body)
