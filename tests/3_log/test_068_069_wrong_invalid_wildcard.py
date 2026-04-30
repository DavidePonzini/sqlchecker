from tests import *
import pytest

ERROR_INVALID = SqlErrors.INVALID_WILDCARD
ERROR_WRONG = SqlErrors.WRONG_WILDCARD

@pytest.mark.parametrize('query,solutions,errors', [
    (
        "SELECT * FROM employees WHERE name LIKE 'John*'",
        ["SELECT * FROM employees WHERE name LIKE 'John%'"],
        [("name LIKE 'John*'",)],
    ),
    (
        "SELECT * FROM employees WHERE name LIKE 'J?hn'",
        ["SELECT * FROM employees WHERE name LIKE 'J_hn'"],
        [("name LIKE 'J?hn'",)],
    ),
])
def test_invalid_wildcard(query, solutions, errors):
    result = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
    )

    assert count_errors(result, ERROR_INVALID) == len(errors)
    assert count_errors(result, ERROR_WRONG) == 0
    for error in errors:
        assert has_error(result, ERROR_INVALID, error)


@pytest.mark.parametrize('query,solutions,errors', [
    (
        "SELECT * FROM employees WHERE name LIKE 'John%'",
        ["SELECT * FROM employees WHERE name LIKE 'John_'"],
        [("name LIKE 'John%'",)],
    ),
    (
        "SELECT * FROM employees WHERE name LIKE 'J_hn'",
        ["SELECT * FROM employees WHERE name LIKE 'J%hn'"],
        [("name LIKE 'J_hn'",)],
    ),
])
def test_wrong_wildcard(query, solutions, errors):
    result = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
    )

    assert count_errors(result, ERROR_INVALID) == 0
    assert count_errors(result, ERROR_WRONG) == len(errors)
    for error in errors:
        assert has_error(result, ERROR_WRONG, error)


@pytest.mark.parametrize('query,solutions', [
    (
        "SELECT * FROM employees WHERE name LIKE 'John*'",
        ["SELECT * FROM employees WHERE name LIKE 'John*'"],
    ),
    (
        "SELECT * FROM employees WHERE name LIKE 'J?hn'",
        ["SELECT * FROM employees WHERE name LIKE 'J?hn'"],
    ),
    ("SELECT * FROM employees WHERE name LIKE 'John%'", []),
    ("SELECT * FROM employees WHERE name LIKE 'J_hn'", []),
    (
        "SELECT * FROM employees WHERE name LIKE 'J_hn_'",
        ["SELECT * FROM employees WHERE name LIKE 'J_hn%'"],
    ),
    (
        "SELECT * FROM employees WHERE name LIKE 'J%hn%'",
        ["SELECT * FROM employees WHERE name LIKE 'J_hn%'"],
    ),
])
def test_correct(query, solutions):
    result = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
    )

    assert count_errors(result, ERROR_INVALID) == 0
    assert count_errors(result, ERROR_WRONG) == 0
