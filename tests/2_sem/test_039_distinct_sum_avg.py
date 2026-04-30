from tests import *
import pytest

ERROR = SqlErrors.DISTINCT_IN_SUM_OR_AVG

@pytest.mark.parametrize('query,solutions,errors', [
    (
        'SELECT SUM(DISTINCT 1 + order_id) AS distinct_order_count FROM orders;',
        [],
        [('SUM(DISTINCT 1 + order_id)',)],
    ),
    (
        'SELECT AVG(DISTINCT amount) AS distinct_avg_amount FROM payments;',
        [],
        [('AVG(DISTINCT amount)',)],
    ),
    (
        'SELECT customer_id, SUM(amount) AS total_amount FROM payments GROUP BY customer_id HAVING SUM(DISTINCT amount) > 1000;',
        [],
        [('SUM(DISTINCT amount)',)],
    ),
    (
        'SELECT SUM(DISTINCT amount), AVG(DISTINCT amount) AS distinct_avg_amount FROM payments;',
        ['SELECT SUM(DISTINCT amount), AVG(amount) AS total_amount FROM payments;'],
        [('AVG(DISTINCT amount)',)],
    ),
])
def test_wrong(query, solutions, errors):
    result = run_test(
        query,
        solutions=solutions,
        detectors=[SemanticErrorDetector],
    )

    assert count_errors(result, ERROR) == len(errors)
    for error in errors:
        assert has_error(result, ERROR, error)


@pytest.mark.parametrize('query', [
    'SELECT SUM(amount) AS total_amount FROM payments;',
    'SELECT AVG(amount) AS avg_amount FROM payments;',
    'SELECT COUNT(DISTINCT customer_id) AS distinct_customer_count FROM orders;',
])
def test_correct(query):
    result = run_test(
        query,
        detectors=[SemanticErrorDetector],
    )

    assert count_errors(result, ERROR) == 0
