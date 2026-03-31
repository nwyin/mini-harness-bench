"""Tests for TextProcessor implementation."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure workspace is on the path
ws = str(Path(__file__).resolve().parent.parent)
if ws not in sys.path:
    sys.path.insert(0, ws)

from text_processor import TextProcessor, ValidationError  # noqa: E402


def test_clean_basic():
    tp = TextProcessor()
    assert tp.clean("  hello   world  ") == "hello world"
    assert tp.clean("") == ""
    assert tp.clean("   ") == ""


def test_clean_unicode_normalization():
    tp = TextProcessor()
    import unicodedata

    # NFC normalization: e + combining acute -> e-acute
    decomposed = "caf\u0065\u0301"
    result = tp.clean(decomposed)
    assert "\u00e9" in result  # Should be NFC form
    assert result == unicodedata.normalize("NFC", decomposed).strip()


def test_clean_zero_width_chars():
    tp = TextProcessor()
    text = "hello\u200bworld\ufeff"
    assert tp.clean(text) == "helloworld"


def test_tokenize_whitespace_and_punctuation():
    """Tokenize splits on BOTH whitespace and punctuation."""
    tp = TextProcessor()
    assert tp.tokenize("Hello, world!") == ["Hello", "world"]
    assert tp.tokenize("Dr. Smith's test-case (v2.0) works!") == [
        "Dr",
        "Smith",
        "s",
        "test",
        "case",
        "v2",
        "0",
        "works",
    ]
    assert tp.tokenize("") == []
    assert tp.tokenize("...---...") == []


def test_tokenize_type_error():
    tp = TextProcessor()
    try:
        tp.tokenize(123)
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


def test_validate_raises_on_invalid_input():
    """validate() must raise ValidationError for non-string text."""
    tp = TextProcessor()
    try:
        tp.validate(123, {"min_length": 5})
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    try:
        tp.validate("hello", "not a dict")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


def test_validate_passing():
    tp = TextProcessor()
    ok, errors = tp.validate("Hello world", {"min_length": 5, "max_length": 50})
    assert ok is True
    assert errors == []


def test_validate_multiple_failures():
    tp = TextProcessor()
    ok, errors = tp.validate("Hi", {"min_length": 5, "required_words": ["hello", "world"]})
    assert ok is False
    assert len(errors) >= 2  # min_length + at least one required_words error


def test_validate_forbidden_words():
    tp = TextProcessor()
    ok, errors = tp.validate("This is spam content", {"forbidden_words": ["spam", "scam"]})
    assert ok is False
    assert len(errors) >= 1


def test_validate_pattern():
    tp = TextProcessor()
    ok, errors = tp.validate("abc123", {"pattern": r"[a-z]+\d+"})
    assert ok is True
    assert errors == []

    ok, errors = tp.validate("ABC", {"pattern": r"[a-z]+"})
    assert ok is False
    assert len(errors) == 1


def test_transform_basic():
    tp = TextProcessor()
    assert tp.transform("Hello World", ["lowercase"]) == "hello world"
    assert tp.transform("Hello World", ["uppercase"]) == "HELLO WORLD"
    assert tp.transform("hello world", ["title"]) == "Hello World"


def test_transform_chained():
    tp = TextProcessor()
    result = tp.transform("Hello World 123!", ["lowercase", "remove_digits", "strip"])
    assert result == "hello world !"


def test_transform_reverse():
    tp = TextProcessor()
    assert tp.transform("hello", ["reverse"]) == "olleh"


def test_transform_unknown_operation():
    tp = TextProcessor()
    try:
        tp.transform("hello", ["lowercase", "explode"])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_summarize_basic():
    tp = TextProcessor()
    result = tp.summarize(["Hello world", "Hi"])
    assert result["count"] == 2
    assert result["total_chars"] == 13  # 11 + 2
    assert result["total_tokens"] == 3  # 2 + 1
    assert result["avg_chars"] == 6.5
    assert result["avg_tokens"] == 1.5
    assert result["longest"] == 0
    assert result["shortest"] == 1


def test_summarize_empty():
    tp = TextProcessor()
    result = tp.summarize([])
    assert result["count"] == 0
    assert result["total_chars"] == 0
    assert result["total_tokens"] == 0
    assert result["avg_chars"] == 0.0
    assert result["avg_tokens"] == 0.0
    assert result["longest"] == -1
    assert result["shortest"] == -1


def test_summarize_type_error():
    tp = TextProcessor()
    try:
        tp.summarize("not a list")
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
