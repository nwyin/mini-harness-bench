import re

MONTHS = {
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
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def parse_date(s: str) -> str:
    s = s.strip()

    # YYYY.MM.DD
    m = re.match(r"^(\d{4})\.(\d{2})\.(\d{2})$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # DD-Mon-YYYY
    m = re.match(r"^(\d{1,2})-([A-Za-z]{3})-(\d{4})$", s)
    if m:
        day = int(m.group(1))
        month = MONTHS[m.group(2).lower()]
        year = int(m.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"

    # Month DD, YYYY
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$", s)
    if m:
        month = MONTHS[m.group(1).lower()]
        day = int(m.group(2))
        year = int(m.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"

    # MM/DD/YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
    if m:
        a, b, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a > 12:
            # Must be DD/MM/YYYY
            return f"{year:04d}-{b:02d}-{a:02d}"
        else:
            # Treat as MM/DD/YYYY
            return f"{year:04d}-{a:02d}-{b:02d}"

    raise ValueError(f"Cannot parse date: {s}")


with open("dates.txt") as f:
    dates = [parse_date(line) for line in f if line.strip()]

with open("output.txt", "w") as f:
    for d in dates:
        f.write(d + "\n")
