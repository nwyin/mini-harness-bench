"""Template compiler: reads config.json and generates compiled templates."""

import json
import sys
from pathlib import Path


def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/config.json")
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("build/templates.txt")
    output.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        print(f"ERROR: Config file {config_path} not found", file=sys.stderr)
        sys.exit(1)

    config = json.loads(config_path.read_text())
    lines = [
        f"Compiled templates for version {config['version']}",
        f"Build mode: {config['build_mode']}",
        f"Features: {', '.join(config['features'])}",
        "",
        "Templates:",
    ]
    for feature in config["features"]:
        lines.append(f"  - {feature}.html: compiled OK")

    output.write_text("\n".join(lines) + "\n")
    print(f"Templates written to {output}")


if __name__ == "__main__":
    main()
