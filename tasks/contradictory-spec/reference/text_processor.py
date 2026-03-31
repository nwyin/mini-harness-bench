"""TextProcessor implementation.

Implements the TextProcessor class according to SPEC.md.
"""

from __future__ import annotations

import re
import string
import unicodedata


class ValidationError(Exception):
    """Raised when validation input is invalid."""

    pass


# Characters treated as token separators (punctuation)
_TOKEN_SEPARATORS = set(".,;:!?\"'()[]{}/-\u2014")


class TextProcessor:
    """Text processing utility class."""

    def clean(self, text: str) -> str:
        """Clean text: strip, collapse whitespace, NFC normalize, remove zero-width chars."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        # Remove zero-width characters
        zero_width = "\u200b\u200c\u200d\ufeff"
        for ch in zero_width:
            text = text.replace(ch, "")
        # NFC normalize
        text = unicodedata.normalize("NFC", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text: str) -> list[str]:
        """Split text into tokens by whitespace and punctuation."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        cleaned = self.clean(text)
        if not cleaned:
            return []
        # Replace all separator punctuation with spaces, then split
        result = []
        current: list[str] = []
        for ch in cleaned:
            if ch in _TOKEN_SEPARATORS or ch.isspace():
                if current:
                    result.append("".join(current))
                    current = []
            else:
                current.append(ch)
        if current:
            result.append("".join(current))
        return result

    def validate(self, text: str, rules: dict) -> tuple[bool, list[str]]:
        """Validate text against rules. Raises ValidationError for invalid input."""
        if not isinstance(text, str) or not isinstance(rules, dict):
            raise ValidationError("text must be a string and rules must be a dict")

        cleaned = self.clean(text)
        errors: list[str] = []

        if "min_length" in rules:
            min_len = rules["min_length"]
            if len(cleaned) < min_len:
                errors.append(f"Text length {len(cleaned)} is less than minimum {min_len}")

        if "max_length" in rules:
            max_len = rules["max_length"]
            if len(cleaned) > max_len:
                errors.append(f"Text length {len(cleaned)} exceeds maximum {max_len}")

        if "required_words" in rules:
            lower_text = cleaned.lower()
            for word in rules["required_words"]:
                if word.lower() not in lower_text:
                    errors.append(f"Required word '{word}' not found in text")

        if "forbidden_words" in rules:
            lower_text = cleaned.lower()
            for word in rules["forbidden_words"]:
                if word.lower() in lower_text:
                    errors.append(f"Forbidden word '{word}' found in text")

        if "pattern" in rules:
            pattern = rules["pattern"]
            if not re.fullmatch(pattern, cleaned):
                errors.append(f"Text does not match pattern '{pattern}'")

        if errors:
            return (False, errors)
        return (True, [])

    def transform(self, text: str, operations: list[str]) -> str:
        """Apply a sequence of transformations to text."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        ops = {
            "uppercase": str.upper,
            "lowercase": str.lower,
            "title": str.title,
            "reverse": lambda s: s[::-1],
            "strip": str.strip,
            "remove_digits": lambda s: re.sub(r"\d", "", s),
            "remove_punctuation": lambda s: s.translate(str.maketrans("", "", string.punctuation)),
        }

        for op in operations:
            if op not in ops:
                raise ValueError(f"Unknown operation: {op}")
            text = ops[op](text)

        return text

    def summarize(self, texts: list[str]) -> dict:
        """Compute summary statistics for a list of texts."""
        if not isinstance(texts, list):
            raise TypeError("texts must be a list")

        valid_texts = [t for t in texts if isinstance(t, str)]

        if not valid_texts:
            return {
                "count": 0,
                "total_chars": 0,
                "total_tokens": 0,
                "avg_chars": 0.0,
                "avg_tokens": 0.0,
                "longest": -1,
                "shortest": -1,
            }

        cleaned = [self.clean(t) for t in valid_texts]
        tokenized = [self.tokenize(t) for t in valid_texts]

        char_counts = [len(c) for c in cleaned]
        token_counts = [len(t) for t in tokenized]

        total_chars = sum(char_counts)
        total_tokens = sum(token_counts)
        count = len(valid_texts)

        return {
            "count": count,
            "total_chars": total_chars,
            "total_tokens": total_tokens,
            "avg_chars": round(total_chars / count, 2),
            "avg_tokens": round(total_tokens / count, 2),
            "longest": char_counts.index(max(char_counts)),
            "shortest": char_counts.index(min(char_counts)),
        }
