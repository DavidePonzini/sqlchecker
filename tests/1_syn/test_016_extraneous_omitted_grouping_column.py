from tests import *
import pytest

ERROR = SqlErrors.EXTRANEOUS_OR_OMITTED_GROUPING_COLUMN

@pytest.mark.parametrize('query', [
    'SELECT id, sum(col2) FROM store GROUP BY id',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 0

@pytest.mark.parametrize('query, errors', [
    (
        'SELECT id, sum(col2) FROM store GROUP BY id, col2',
        [('col2', 'ONLY IN GROUP BY')],
    ),
    (
        'SELECT id, SUM(col2) FROM store GROUP BY 1, 2',
        [('SUM(col2)', 'AGGREGATED IN GROUP BY')],
    ),
    (
        'SELECT id, SUM(col2) FROM store GROUP BY id, SUM(col2)',
        [('SUM(col2)', 'AGGREGATED IN GROUP BY')],
    ),
    (
        'SELECT id, col2, sum(col3) FROM store GROUP BY id',
        [('col2', 'ONLY IN SELECT')],
    ),
    (
        'SELECT id, col2, sum(col3) FROM store GROUP BY id, col4',
        [('col2', 'ONLY IN SELECT'), ('col4', 'ONLY IN GROUP BY')],
    ),
])
def test_wrong(query, errors):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == len(errors)
    for error in errors:
        assert has_error(detected_errors, ERROR, error)
