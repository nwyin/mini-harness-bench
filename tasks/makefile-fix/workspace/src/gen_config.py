"""Config generator: produces build/config.json."""

import json
import sys
from pathlib import Path


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/config.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "version": "1.0.0",
        "build_mode": "release",
        "features": ["logging", "metrics", "caching"],
        "source_dir": "src",
        "build_dir": "build",
    }
    output.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Config written to {output}")


if __name__ == "__main__":
    main()
