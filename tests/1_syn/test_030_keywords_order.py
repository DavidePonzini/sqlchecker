import pytest
from tests import *

ERROR = SqlErrors.CONFUSED_ORDER_OF_KEYWORDS


@pytest.mark.parametrize('query', [
    'SELECT col1 FROM table1 WHERE col2 = 10 GROUP BY col1 HAVING COUNT(col2) > 5 ORDER BY col1 LIMIT 10 OFFSET 5',
    'SELECT col1, COUNT(col2) FILTER (WHERE col3 = 1) as count_col FROM table1 WHERE col4 = 2',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 0


@pytest.mark.parametrize('query, keywords', [
    (
        'SELECT col1 WHERE col2 = 10 FROM table1',
        ['SELECT', 'WHERE', 'FROM'],
    ),
    (
        'SELECT col1 FROM table1 WHERE col2 IN (SELECT col2 GROUP BY col3 FROM table2 ORDER BY col2 LIMIT 5 OFFSET 2 WHERE col3 = 20)',
        ['SELECT', 'GROUP BY', 'FROM', 'ORDER BY', 'LIMIT', 'OFFSET', 'WHERE'],
    ),
])
def test_wrong(query, keywords):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 1
    assert has_error(detected_errors, ERROR, (keywords,))
