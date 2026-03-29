#!/usr/bin/env python3
"""Encryption CLI tool supporting Caesar cipher and ROT13."""

import argparse
import sys  # noqa: F401


def build_parser():
    parser = argparse.ArgumentParser(description="Encrypt text files using Caesar cipher or ROT13")
    parser.add_argument("--method", choices=["caesar", "rot13"], required=True, help="Encryption method")
    parser.add_argument("--shift", type=int, help="Shift value for Caesar cipher")
    parser.add_argument("--input-file", required=True, help="Path to input file")
    parser.add_argument("--output-file", required=True, help="Path to output file")
    return parser


def caesar_encrypt(text, shift):
    """Encrypt text using Caesar cipher with the given shift."""
    # TODO: implement this
    raise NotImplementedError


def rot13_encrypt(text):
    """Encrypt text using ROT13."""
    # TODO: implement this
    raise NotImplementedError


def main():
    parser = build_parser()
    args = parser.parse_args()  # noqa: F841

    # TODO: validate arguments, read input, encrypt, write output
    raise NotImplementedError


if __name__ == "__main__":
    main()
