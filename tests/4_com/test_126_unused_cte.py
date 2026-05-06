from tests import *
import pytest

ERROR = SqlErrors.UNUSED_CTE


@pytest.mark.parametrize('query, errors', [
    (
        'WITH cte AS (SELECT a FROM table1) SELECT * FROM table2;',
        [('SELECT a FROM table1',)],
    ),
    (
        'WITH cte1 AS (SELECT a FROM table1), cte2 AS (SELECT b FROM table2) SELECT * FROM cte1;',
        [('SELECT b FROM table2',)],
    ),
    (
        'WITH cte1 AS (SELECT a FROM table1), cte2 AS (SELECT b FROM table2) SELECT * FROM table3;',
        [('SELECT a FROM table1',), ('SELECT b FROM table2',)],
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
    'WITH cte AS (SELECT a FROM table1) SELECT * FROM cte;',
    'WITH cte1 AS (SELECT a FROM table1), cte2 AS (SELECT a FROM table2) SELECT * FROM cte1 join cte2 on true;',
    'WITH cte1 AS (SELECT a FROM table1), cte2 AS (SELECT a FROM cte1) SELECT * FROM cte2;',
    'SELECT * FROM table1;',
])
def test_correct(query):
    result = run_test(
        query,
        detectors=[ComplicationDetector],
    )

    assert count_errors(result, ERROR) == 0
