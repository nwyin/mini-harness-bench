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
    # TODO: implement this by reverse-engineering the server's decode_message()
    raise NotImplementedError("encode_message is not yet implemented")
