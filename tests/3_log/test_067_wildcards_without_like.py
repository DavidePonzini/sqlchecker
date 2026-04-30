from tests import *
import pytest

ERROR = SqlErrors.WILDCARDS_WITHOUT_LIKE

@pytest.mark.parametrize('query,solutions,errors', [
    (
        "SELECT * FROM employees WHERE name = 'John%'",
        ["SELECT * FROM employees WHERE name LIKE 'John%'"],
        [("name = 'John%'",)],
    ),
    (
        "SELECT * FROM employees WHERE name = 'John_Doe'",
        ["SELECT * FROM employees WHERE name LIKE 'John_Doe'"],
        [("name = 'John_Doe'",)],
    ),
    (
        "SELECT * FROM employees WHERE 'John%' = name",
        ["SELECT * FROM employees WHERE name LIKE 'John%'"],
        [("'John%' = name",)],
    ),
    (
        "SELECT * FROM employees WHERE name = 'John%' or name = 'Jane_'",
        ["SELECT * FROM employees WHERE name LIKE 'John%'", "SELECT * FROM employees WHERE name = 'Jane_'"],
        [("name = 'John%'",)],
    ),
])
def test_wrong(query, solutions, errors):
    result = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
    )

    assert count_errors(result, ERROR) == len(errors)
    for error in errors:
        assert has_error(result, ERROR, error)


@pytest.mark.parametrize('query,solutions', [
    ("SELECT * FROM employees WHERE name = 'JohnDoe'", []),
    ("SELECT * FROM employees WHERE name LIKE 'John%'", []),
    ("SELECT * FROM employees WHERE name = 'JohnDoe'", []),
    (
        "SELECT * FROM employees WHERE name = 'John_Doe'",
        ["SELECT * FROM employees WHERE name = 'John_Doe'"],
    ),
    (
        "SELECT * FROM employees WHERE status = '100%'",
        ["SELECT * FROM employees WHERE status = '100%'"],
    ),
])
def test_correct(query, solutions):
    result = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
    )

    assert count_errors(result, ERROR) == 0
