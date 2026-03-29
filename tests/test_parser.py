from mhb.evaluation.parser import parse_pytest_output, parse_shell_checks


def test_parse_pytest_passed():
    output = "tests/test_foo.py::test_bar PASSED\ntests/test_foo.py::test_baz FAILED\n"
    results = parse_pytest_output(output)
    assert len(results) == 2
    assert results[0]["name"] == "test_bar"
    assert results[0]["status"] == "passed"
    assert results[1]["name"] == "test_baz"
    assert results[1]["status"] == "failed"


def test_parse_pytest_empty():
    assert parse_pytest_output("") == []


def test_parse_pytest_noise():
    output = "===== 2 passed in 0.5s =====\nsome other output\ntests/test_a.py::test_x PASSED\n"
    results = parse_pytest_output(output)
    assert len(results) == 1
    assert results[0]["name"] == "test_x"
    assert results[0]["status"] == "passed"


def test_parse_pytest_with_percentage():
    output = "tests/test_foo.py::test_bar PASSED [ 50%]\ntests/test_foo.py::test_baz FAILED [100%]\n"
    results = parse_pytest_output(output)
    assert len(results) == 2
    assert results[0]["name"] == "test_bar"
    assert results[0]["status"] == "passed"
    assert results[1]["status"] == "failed"


def test_parse_shell_checks():
    output = "PASS: check_file_exists\nFAIL: check_content_valid\nPASS: check_permissions\n"
    results = parse_shell_checks(output)
    assert len(results) == 3
    assert results[0] == {"name": "check_file_exists", "status": "passed"}
    assert results[1] == {"name": "check_content_valid", "status": "failed"}
    assert results[2] == {"name": "check_permissions", "status": "passed"}


def test_parse_shell_checks_empty():
    assert parse_shell_checks("") == []
