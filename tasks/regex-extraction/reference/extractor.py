#!/usr/bin/env python3
"""Extract structured fields from unstructured text."""

import re

MONTH_ABBR = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

MONTH_FULL = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def extract_emails(text):
    """Extract all valid email addresses, lowercased, deduplicated, sorted."""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    matches = re.findall(pattern, text)
    unique = sorted(set(m.lower() for m in matches))
    return unique


def extract_dates(text):
    """Extract dates in multiple formats, normalize to YYYY-MM-DD, deduplicated, sorted."""
    dates = set()

    # YYYY-MM-DD
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            dates.add(f"{y:04d}-{mo:02d}-{d:02d}")

    # MM/DD/YYYY
    for m in re.finditer(r"\b(\d{2})/(\d{2})/(\d{4})\b", text):
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            dates.add(f"{y:04d}-{mo:02d}-{d:02d}")

    # DD-Mon-YYYY
    for m in re.finditer(r"\b(\d{1,2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{4})\b", text, re.I):
        d, mon, y = int(m.group(1)), m.group(2).lower()[:3], int(m.group(3))
        mo = MONTH_ABBR.get(mon)
        if mo and 1 <= d <= 31:
            dates.add(f"{y:04d}-{mo:02d}-{d:02d}")

    # Month DD, YYYY
    month_names = "|".join(MONTH_FULL.keys())
    for m in re.finditer(rf"\b({month_names})\s+(\d{{1,2}}),?\s+(\d{{4}})\b", text, re.I):
        mon, d, y = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        mo = MONTH_FULL.get(mon)
        if mo and 1 <= d <= 31:
            dates.add(f"{y:04d}-{mo:02d}-{d:02d}")

    return sorted(dates)


def extract_phone_numbers(text):
    """Extract US phone numbers, normalize to (XXX) XXX-XXXX, deduplicated, sorted."""
    patterns = [
        r"\+?1?[-.\s]?\((\d{3})\)\s*(\d{3})[-.](\d{4})",
        r"\+?1?[-.\s]?(\d{3})[-.](\d{3})[-.](\d{4})",
        r"\b(\d{3})(\d{3})(\d{4})\b",
    ]

    phones = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            area, prefix, line = m.group(1), m.group(2), m.group(3)
            phones.add(f"({area}) {prefix}-{line}")

    return sorted(phones)


def extract_ipv4(text):
    """Extract valid IPv4 addresses, deduplicated, sorted by numeric value."""
    pattern = r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b"
    ips = set()
    for m in re.finditer(pattern, text):
        octets = [int(m.group(i)) for i in range(1, 5)]
        if all(0 <= o <= 255 for o in octets):
            ips.add(".".join(str(o) for o in octets))

    def ip_sort_key(ip):
        return tuple(int(p) for p in ip.split("."))

    return sorted(ips, key=ip_sort_key)


def extract_urls(text):
    """Extract URLs starting with http:// or https://, deduplicated, sorted."""
    pattern = r"https?://[^\s<>\"',)}\]]+"
    # Strip trailing punctuation that is likely not part of the URL
    matches = set()
    for m in re.finditer(pattern, text):
        url = m.group(0).rstrip(".,;:!?")
        matches.add(url)
    return sorted(matches)
