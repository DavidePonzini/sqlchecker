import pytest
from tests import *

ERROR = SqlErrors.USING_WHERE_TWICE


@pytest.mark.parametrize('query', [
    'SELECT col1 WHERE col2 = 1',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 0


@pytest.mark.parametrize('query, errors', [
    (
        'SELECT col1 WHERE col2 = 1 WHERE col3 = 2',
        [('SELECT col1 WHERE col2 = 1 WHERE col3 = 2', 2)],
    ),
    (
        '''
    SELECT col1, (SELECT col2 WHERE col3 = 1 WHERE col4 = 2) as subquery_col
    FROM table1
    WHERE col5 = 3
    ''',
        [('SELECT col2 WHERE col3 = 1 WHERE col4 = 2', 2)],
    ),
    (
        '''
    SELECT col1, (SELECT col2 WHERE col3 = 1 WHERE col4 = 2) as subquery_col1, (SELECT col5 WHERE col6 = 3 WHERE col7 = 4 WHERE col8 = 5) as subquery_col2
    FROM table1
    WHERE col8 = 5 WHERE col9 = 6
    ''',
        [
            ('SELECT col2 WHERE col3 = 1 WHERE col4 = 2', 2),
            ('SELECT col5 WHERE col6 = 3 WHERE col7 = 4 WHERE col8 = 5', 3),
            ('SELECT col1, (SELECT col2 WHERE col3 = 1 WHERE col4 = 2) as subquery_col1, (SELECT col5 WHERE col6 = 3 WHERE col7 = 4 WHERE col8 = 5) as subquery_col2\n    FROM table1\n    WHERE col8 = 5 WHERE col9 = 6', 2),
        ],
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
