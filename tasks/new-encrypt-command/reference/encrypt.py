#!/usr/bin/env python3
"""Encryption CLI tool supporting Caesar cipher and ROT13."""

import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(description="Encrypt text files using Caesar cipher or ROT13")
    parser.add_argument("--method", choices=["caesar", "rot13"], required=True, help="Encryption method")
    parser.add_argument("--shift", type=int, help="Shift value for Caesar cipher")
    parser.add_argument("--input-file", required=True, help="Path to input file")
    parser.add_argument("--output-file", required=True, help="Path to output file")
    return parser


def caesar_encrypt(text, shift):
    """Encrypt text using Caesar cipher with the given shift."""
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


def rot13_encrypt(text):
    """Encrypt text using ROT13."""
    return caesar_encrypt(text, 13)


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.method == "caesar" and args.shift is None:
        print("Error: --shift is required when using caesar method", file=sys.stderr)
        sys.exit(1)

    with open(args.input_file) as f:
        plaintext = f.read()

    if args.method == "caesar":
        ciphertext = caesar_encrypt(plaintext, args.shift)
    else:
        ciphertext = rot13_encrypt(plaintext)

    with open(args.output_file, "w") as f:
        f.write(ciphertext)


if __name__ == "__main__":
    main()
