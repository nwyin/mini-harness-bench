import os
import subprocess
import sys
import tempfile


def run_encrypt(*args):
    """Run encrypt.py with given arguments and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, "encrypt.py", *args],
        capture_output=True,
        text=True,
    )


def encrypt_text(method, text, shift=None):
    """Helper: write text to a temp file, encrypt it, return the result."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as inp:
        inp.write(text)
        inp_path = inp.name
    out_path = inp_path + ".enc"
    try:
        args = ["--method", method, "--input-file", inp_path, "--output-file", out_path]
        if shift is not None:
            args += ["--shift", str(shift)]
        result = run_encrypt(*args)
        assert result.returncode == 0, f"encrypt.py failed: {result.stderr}"
        with open(out_path) as f:
            return f.read()
    finally:
        os.unlink(inp_path)
        if os.path.exists(out_path):
            os.unlink(out_path)


def test_caesar_basic():
    """Caesar cipher with shift=3 on simple lowercase text."""
    assert encrypt_text("caesar", "abc", shift=3) == "def"


def test_caesar_wrapping():
    """Caesar cipher wraps around z -> a."""
    assert encrypt_text("caesar", "xyz", shift=3) == "abc"


def test_caesar_mixed_case():
    """Caesar cipher preserves case."""
    assert encrypt_text("caesar", "Hello World", shift=1) == "Ifmmp Xpsme"


def test_caesar_non_alpha():
    """Caesar cipher leaves non-alphabetic characters unchanged."""
    assert encrypt_text("caesar", "Hello, World! 123", shift=5) == "Mjqqt, Btwqi! 123"


def test_caesar_large_shift():
    """Caesar cipher with shift > 26 wraps correctly."""
    assert encrypt_text("caesar", "abc", shift=29) == "def"


def test_rot13_basic():
    """ROT13 on simple text."""
    assert encrypt_text("rot13", "Hello") == "Uryyb"


def test_rot13_roundtrip():
    """Applying ROT13 twice returns the original text."""
    original = "The quick brown fox jumps over 13 lazy dogs!"
    encrypted = encrypt_text("rot13", original)
    decrypted = encrypt_text("rot13", encrypted)
    assert decrypted == original


def test_caesar_missing_shift():
    """Caesar method without --shift should exit with code 1."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as inp:
        inp.write("test")
        inp_path = inp.name
    try:
        result = run_encrypt(
            "--method",
            "caesar",
            "--input-file",
            inp_path,
            "--output-file",
            inp_path + ".enc",
        )
        assert result.returncode != 0
    finally:
        os.unlink(inp_path)
        if os.path.exists(inp_path + ".enc"):
            os.unlink(inp_path + ".enc")
