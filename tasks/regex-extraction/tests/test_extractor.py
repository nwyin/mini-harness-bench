import os
import sys

import pytest

sys.path.insert(0, os.getcwd())


def load_test_data(name):
    """Load a test data file from the hidden test data directory."""
    test_data_dir = os.path.join(os.path.dirname(__file__), "data")
    with open(os.path.join(test_data_dir, name)) as f:
        return f.read()


@pytest.fixture
def extractor():
    import extractor

    return extractor


def test_extract_emails(extractor):
    """Extract and deduplicate emails from test data."""
    text = load_test_data("test_emails.txt")
    emails = extractor.extract_emails(text)
    assert "alice@example.com" in emails
    assert "bob.jones@company.org" in emails
    assert "carol_99@sub.domain.co.uk" in emails
    assert "dev+tag@startup.io" in emails
    assert "human.resources@big-corp.com" in emails
    # Deduplicated: alice appears once
    assert emails.count("alice@example.com") == 1
    # All lowercase
    assert all(e == e.lower() for e in emails)


def test_extract_emails_sorted(extractor):
    """Extracted emails should be sorted alphabetically."""
    text = load_test_data("test_emails.txt")
    emails = extractor.extract_emails(text)
    assert emails == sorted(emails)


def test_extract_dates(extractor):
    """Extract dates in multiple formats and normalize to YYYY-MM-DD."""
    text = load_test_data("test_dates.txt")
    dates = extractor.extract_dates(text)
    assert "2024-01-15" in dates
    assert "2024-01-30" in dates
    assert "2024-02-15" in dates
    assert "2024-03-01" in dates
    assert "2024-06-15" in dates
    assert "2024-12-25" in dates
    assert "2024-11-10" in dates
    # 2024-03-01 appears twice (March 1 and ISO format) but should be deduplicated
    assert dates.count("2024-03-01") == 1


def test_extract_dates_sorted(extractor):
    """Extracted dates should be sorted chronologically."""
    text = load_test_data("test_dates.txt")
    dates = extractor.extract_dates(text)
    assert dates == sorted(dates)


def test_extract_phone_numbers(extractor):
    """Extract phone numbers in various formats and normalize."""
    text = load_test_data("test_phones.txt")
    phones = extractor.extract_phone_numbers(text)
    assert "(212) 555-1234" in phones
    assert "(212) 555-1235" in phones
    assert "(212) 555-1236" in phones
    assert "(800) 555-9999" in phones
    assert "(312) 555-4444" in phones
    assert "(415) 555-0000" in phones
    # Deduplicated
    assert phones.count("(212) 555-1234") == 1


def test_extract_ipv4(extractor):
    """Extract valid IPv4 addresses and reject invalid ones."""
    text = load_test_data("test_ips.txt")
    ips = extractor.extract_ipv4(text)
    assert "8.8.4.4" in ips
    assert "8.8.8.8" in ips
    assert "10.0.0.1" in ips
    assert "192.168.1.100" in ips
    assert "127.0.0.1" in ips
    # 999.999.999.999 is invalid and should be excluded
    assert "999.999.999.999" not in ips
    # Deduplicated
    assert ips.count("8.8.8.8") == 1


def test_extract_ipv4_sorted(extractor):
    """IPs should be sorted by numeric value."""
    text = load_test_data("test_ips.txt")
    ips = extractor.extract_ipv4(text)
    # 8.8.4.4 should come before 10.0.0.1
    assert ips.index("8.8.4.4") < ips.index("10.0.0.1")
    assert ips.index("10.0.0.1") < ips.index("127.0.0.1")


def test_extract_urls(extractor):
    """Extract URLs starting with http:// or https://."""
    text = load_test_data("test_urls.txt")
    urls = extractor.extract_urls(text)
    assert "https://docs.example.com/v2/guide" in urls
    assert "https://api.example.com/v1/users?active=true" in urls
    assert "http://wiki.internal.corp/legacy" in urls
    assert "https://cdn.example.com/assets/logo.png" in urls
    assert "http://example.com" in urls
    # Deduplicated
    assert urls.count("https://docs.example.com/v2/guide") == 1
