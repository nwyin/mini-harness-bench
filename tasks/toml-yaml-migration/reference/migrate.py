#!/usr/bin/env python3
"""Convert TOML configuration to YAML format."""

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import yaml


def main():
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    with open("config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main()
