# TextProcessor API Specification

## Overview

The `TextProcessor` class provides a suite of text processing utilities. It is
designed to be used in data ingestion pipelines where text needs to be cleaned,
tokenized, validated, transformed, and summarized.

All methods operate on plain Unicode strings. The class is stateless — each
method call is independent.

### Tokenization

The `tokenize()` method splits text into tokens by whitespace. Leading and
trailing whitespace is stripped before splitting. Empty strings return an empty
list.

### Import

```python
from text_processor import TextProcessor, ValidationError
```

---

## API Reference

### `TextProcessor()`

Constructor. Takes no arguments.

### `clean(text: str) -> str`

Clean the input text:
1. Strip leading and trailing whitespace.
2. Collapse multiple consecutive whitespace characters (spaces, tabs, newlines)
   into a single space.
3. Normalize Unicode characters to NFC form.
4. Remove any zero-width characters (U+200B, U+200C, U+200D, U+FEFF).

**Returns:** The cleaned string.

**Edge cases:**
- Empty string input returns empty string.
- String with only whitespace returns empty string.

### `tokenize(text: str) -> list[str]`

Split text into tokens.

The text is first cleaned (using the same logic as `clean()`), then split into
tokens. Tokens are separated by whitespace and punctuation characters. The
following characters are treated as token separators and are NOT included in
the output: `. , ; : ! ? " ' ( ) [ ] { } / \ - —`

**Returns:** A list of non-empty token strings.

**Edge cases:**
- Empty string returns `[]`.
- String with only whitespace/punctuation returns `[]`.

### `validate(text: str, rules: dict) -> tuple[bool, list[str]]`

Validate text against a set of rules. Available rules:

- `"min_length"` (int): text must have at least this many characters (after cleaning).
- `"max_length"` (int): text must have at most this many characters (after cleaning).
- `"required_words"` (list[str]): all listed words must appear in the text (case-insensitive).
- `"forbidden_words"` (list[str]): none of the listed words may appear (case-insensitive).
- `"pattern"` (str): text must match this regex pattern (full match).

For invalid input, this method should raise a `ValidationError` with a
descriptive message. Invalid input means: `text` is not a string, or `rules`
is not a dict.

For valid input that fails validation, return `(False, errors)` where `errors`
is a list of human-readable error message strings describing each rule
violation.

For valid input that passes all rules, return `(True, [])`.

**Edge cases:**
- Empty rules dict: always passes → `(True, [])`.
- If multiple rules fail, all violations are reported (not just the first).

### `transform(text: str, operations: list[str]) -> str`

Apply a sequence of transformations to the text, in order. Supported operations:

- `"uppercase"`: convert to uppercase
- `"lowercase"`: convert to lowercase
- `"title"`: convert to title case
- `"reverse"`: reverse the string
- `"strip"`: strip leading/trailing whitespace
- `"remove_digits"`: remove all digit characters
- `"remove_punctuation"`: remove all ASCII punctuation characters

Operations are applied left-to-right. If an unknown operation is encountered,
raise a `ValueError` with a message listing the unknown operation.

**Returns:** The transformed string.

### `summarize(texts: list[str]) -> dict`

Compute summary statistics for a list of texts.

**Returns:** A dictionary with the following keys:
- `"count"`: number of texts (int)
- `"total_chars"`: total character count across all texts (int), using cleaned text
- `"total_tokens"`: total token count across all texts (int), using tokenize()
- `"avg_chars"`: average character count per text (float, rounded to 2 decimal places), 0.0 if empty
- `"avg_tokens"`: average token count per text (float, rounded to 2 decimal places), 0.0 if empty
- `"longest"`: index of the longest text by character count (int), or -1 if empty
- `"shortest"`: index of the shortest text by character count (int), or -1 if empty

**Edge cases:**
- Empty list returns all zeroes/defaults as described above.
- Ties in longest/shortest: return the first (lowest index).

---

## Error Handling

- `clean()` and `tokenize()`: if input is not a string, raise `TypeError`.
- `validate()`: if input is invalid (non-string text or non-dict rules),
  return `(False, ["Invalid input: text must be a string and rules must be a dict"])`.
- `transform()`: if input is not a string, raise `TypeError`. Unknown
  operations raise `ValueError`.
- `summarize()`: if input is not a list, raise `TypeError`. Non-string items
  in the list are skipped.

---

## `ValidationError`

```python
class ValidationError(Exception):
    """Raised when validation input is invalid."""
    pass
```

---

## Examples

### Example: tokenize

```python
tp = TextProcessor()
tp.tokenize("Hello, world!")
# → ["Hello", "world"]

tp.tokenize("Dr. Smith's test-case (v2.0) works!")
# → ["Dr", "Smith", "s", "test", "case", "v2", "0", "works"]

tp.tokenize("")
# → []
```

### Example: validate

```python
tp = TextProcessor()

# Valid text, passing
tp.validate("Hello world", {"min_length": 5})
# → (True, [])

# Valid text, failing
tp.validate("Hi", {"min_length": 5, "max_length": 100})
# → (False, ["Text length 2 is less than minimum 5"])

# Invalid input
tp.validate(123, {"min_length": 5})
# → raises ValidationError("text must be a string")
```

### Example: transform

```python
tp = TextProcessor()
tp.transform("Hello World 123!", ["lowercase", "remove_digits", "strip"])
# → "hello world !"
```

### Example: summarize

```python
tp = TextProcessor()
tp.summarize(["Hello world", "Hi"])
# → {
#     "count": 2,
#     "total_chars": 13,
#     "total_tokens": 3,
#     "avg_chars": 6.5,
#     "avg_tokens": 1.5,
#     "longest": 0,
#     "shortest": 1
# }
```
