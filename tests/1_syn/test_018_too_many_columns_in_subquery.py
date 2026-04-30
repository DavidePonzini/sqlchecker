from tests import *
import pytest

ERROR = SqlErrors.TOO_MANY_COLUMNS_IN_SUBQUERY


@pytest.mark.parametrize('query, subquery', [
    (
        'SELECT col1, col2 FROM main WHERE col3 IN (SELECT col4, col5 FROM subq)',
        'SELECT col4, col5 FROM subq',
    ),
    (
        'SELECT col1 FROM main WHERE col2 = (SELECT col3, col4 FROM subq)',
        'SELECT col3, col4 FROM subq',
    ),
    (
        'SELECT (SELECT col1, col2 FROM subq) AS subquery_result FROM main',
        'SELECT col1, col2 FROM subq',
    ),
])
def test_wrong(query, subquery):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 1
    assert has_error(detected_errors, ERROR, (subquery, 1))


@pytest.mark.parametrize('query', [
    'SELECT col1 FROM main WHERE EXISTS (SELECT col2, col3 FROM subq)',
    'SELECT col1 FROM main WHERE col2 = (SELECT col3 FROM subq)',
    'SELECT col1 FROM (SELECT col2, col3 FROM subq) AS subquery_alias',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 0
