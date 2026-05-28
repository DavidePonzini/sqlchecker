from tests import *
import pytest

ERROR = SqlErrors.LIKE_WITHOUT_WILDCARDS


@pytest.mark.parametrize('query, errors', [
    (
        "SELECT * FROM employees WHERE name LIKE 'JohnDoe'",
        [("name LIKE 'JohnDoe'",)],
    ),
])
def test_wrong(query, errors):
    result = run_test(
        query,
        detectors=[ComplicationDetector],
    )

    assert count_errors(result, ERROR) == len(errors)
    for error in errors:
        assert has_error(result, ERROR, error)


@pytest.mark.parametrize('query', [
    "SELECT * FROM employees WHERE name LIKE 'John_Doe'",
    "SELECT * FROM employees WHERE name LIKE 'John%'",
])
def test_correct(query):
    result = run_test(
        query,
        detectors=[ComplicationDetector],
    )

    assert count_errors(result, ERROR) == 0
