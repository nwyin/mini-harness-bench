#!/usr/bin/env python3
"""Parse semi-structured application logs into structured JSON."""

import json
import re
import sys

REQUEST_PATTERN = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] "
    r"(\w+) "
    r"([\w.]+): "
    r"(GET|POST|PUT|DELETE|PATCH|HEAD) "
    r"(\S+) "
    r"(\d+) "
    r"(\d+)ms$"
)

STANDARD_PATTERN = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] " r"(\w+) " r"([\w.]+): " r"(.+)$")

TRACEBACK_PATTERN = re.compile(r"^\s+Traceback: (.+)$")


def parse_timestamp(ts_str):
    """Convert 'YYYY-MM-DD HH:MM:SS' to 'YYYY-MM-DDTHH:MM:SS'."""
    return ts_str.replace(" ", "T")


def parse_log(log_text):
    """Parse log text into a list of structured entries."""
    entries = []
    lines = log_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue

        # Try request pattern first (more specific)
        m = REQUEST_PATTERN.match(line)
        if m:
            entries.append(
                {
                    "timestamp": parse_timestamp(m.group(1)),
                    "level": m.group(2).upper(),
                    "module": m.group(3),
                    "message": f"{m.group(4)} {m.group(5)} {m.group(6)} {m.group(7)}ms",
                    "type": "request",
                    "method": m.group(4),
                    "path": m.group(5),
                    "status_code": int(m.group(6)),
                    "response_time_ms": int(m.group(7)),
                }
            )
            i += 1
            continue

        # Try standard pattern
        m = STANDARD_PATTERN.match(line)
        if m:
            timestamp = parse_timestamp(m.group(1))
            level = m.group(2).upper()
            module = m.group(3)
            message = m.group(4)

            # Check if next line is a traceback
            entry_type = "error" if level == "ERROR" else "standard"
            entry = {
                "timestamp": timestamp,
                "level": level,
                "module": module,
                "message": message,
                "type": entry_type,
            }

            if i + 1 < len(lines):
                tb_match = TRACEBACK_PATTERN.match(lines[i + 1])
                if tb_match:
                    entry["type"] = "error"
                    entry["traceback"] = tb_match.group(1)
                    i += 1

            entries.append(entry)
            i += 1
            continue

        # Skip unrecognized lines
        i += 1

    return entries


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.log> <output.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        log_text = f.read()

    entries = parse_log(log_text)

    with open(sys.argv[2], "w") as f:
        json.dump(entries, f, indent=2)


if __name__ == "__main__":
    main()
