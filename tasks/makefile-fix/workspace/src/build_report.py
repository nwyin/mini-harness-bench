"""Report builder: combines lint report, config, and templates into final output."""

import json
import sys
from pathlib import Path


def main():
    build_dir = Path("build")
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else build_dir / "output.txt"
    output.parent.mkdir(parents=True, exist_ok=True)

    lint_report = build_dir / "lint_report.txt"
    config_file = build_dir / "config.json"
    templates_file = build_dir / "templates.txt"

    missing = []
    for f in [lint_report, config_file, templates_file]:
        if not f.exists():
            missing.append(str(f))

    if missing:
        print(f"ERROR: Missing input files: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    config = json.loads(config_file.read_text())

    sections = [
        "=" * 60,
        f"BUILD REPORT - v{config['version']}",
        "=" * 60,
        "",
        "--- Lint Results ---",
        lint_report.read_text().strip(),
        "",
        "--- Config ---",
        json.dumps(config, indent=2),
        "",
        "--- Templates ---",
        templates_file.read_text().strip(),
        "",
        "=" * 60,
        "BUILD COMPLETE",
        "=" * 60,
    ]

    output.write_text("\n".join(sections) + "\n")
    print(f"Build report written to {output}")


if __name__ == "__main__":
    main()
