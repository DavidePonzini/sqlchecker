import pytest
from tests import *

ERROR = SqlErrors.OMITTED_FROM_CLAUSE


@pytest.mark.parametrize('query, errors', [
    ('SELECT col1', [('SELECT col1',)]),
    (
        '''
    WITH cte AS (
        SELECT no_col
    )
    SELECT col1 FROM cte
    ''',
        [('SELECT no_col',)],
    ),
    (
        'SELECT col1 AS sub_col WHERE col2 IN (SELECT no_col)',
        [('SELECT col1 AS sub_col WHERE col2 IN (SELECT no_col)',), ('SELECT no_col',)],
    ),
    (
        'SELECT col1 AS sub_col FROM table1 WHERE col2 IN (SELECT no_col)',
        [('SELECT no_col',)],
    ),
    (
        'SELECT col1 AS sub_col WHERE col2 IN (SELECT col3 FROM table2)',
        [('SELECT col1 AS sub_col WHERE col2 IN (SELECT col3 FROM table2)',)],
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


@pytest.mark.parametrize('query', [
    'SELECT 1 + 2',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 0
