import pytest
from tests import *

ERROR = SqlErrors.DUPLICATE_CLAUSE


@pytest.mark.parametrize('query', [
    'SELECT col1 FROM table1 WHERE col2 = 10 GROUP BY col1 HAVING COUNT(*) > 1',
    'SELECT col1 FROM table1 WHERE col2 IN (SELECT col3 FROM table2) GROUP BY col1 HAVING COUNT(*) > 1',
    'SELECT col1 FROM table1 JOIN table2 ON table1.id = table2.id JOIN table3 ON table2.id = table3.id',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 0


@pytest.mark.parametrize('query, errors', [
    (
        'SELECT col1 FROM table1 WHERE col2 = 10 WHERE col3 = 20',
        [('WHERE', 2)],
    ),
    (
        'SELECT col1 FROM table1 WHERE col2 = 10 WHERE col3 = 20 GROUP BY col1 GROUP BY col2 COUNT(*) > 1 HAVING SUM(col4) < 100 GROUP BY col5',
        [('WHERE', 2), ('GROUP BY', 3)],
    ),
    (
        'SELECT col1 SELECT col2 FROM table1 WHERE col2 IN (SELECT col3 FROM table2 WHERE col4 = 30 WHERE col5 = 40 GROUP BY col3 GROUP BY col4 GROUP BY id HAVING COUNT(*) > 2) GROUP BY col3 GROUP BY col4 HAVING COUNT(*) > 1',
        [('SELECT', 2), ('WHERE', 2), ('GROUP BY', 2), ('GROUP BY', 3)],
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
