from __future__ import annotations

import re


def parse_pytest_output(output: str) -> list[dict]:
    results = []
    for line in output.splitlines():
        # Match verbose pytest lines like:
        # "path/to/test.py::test_name PASSED [ 7%]"
        # "test_name PASSED"
        m = re.match(r"^(.*?)\s+(PASSED|FAILED|ERROR|SKIPPED)\s*(\[.*\])?\s*$", line.strip())
        if m:
            name = m.group(1).strip()
            # Extract just the test name (after last ::)
            if "::" in name:
                name = name.rsplit("::", 1)[-1]
            status = "passed" if m.group(2) == "PASSED" else "failed"
            results.append({"name": name, "status": status})
    return results


def parse_shell_checks(output: str) -> list[dict]:
    results = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("PASS:"):
            name = line[5:].strip()
            results.append({"name": name, "status": "passed"})
        elif line.startswith("FAIL:"):
            name = line[5:].strip()
            results.append({"name": name, "status": "failed"})
    return results
