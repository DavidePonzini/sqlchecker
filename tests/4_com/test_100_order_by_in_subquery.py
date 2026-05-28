from tests import *
import pytest

ERROR = SqlErrors.ORDER_BY_IN_SUBQUERY


@pytest.mark.parametrize('query, errors', [
    (
        'SELECT * FROM employees WHERE id IN (SELECT employee_id FROM orders ORDER BY order_date)',
        [('SELECT employee_id FROM orders ORDER BY order_date',)],
    ),
    (
        'SELECT * FROM employees WHERE id IN (SELECT employee_id FROM orders WHERE product_id IN (SELECT id FROM products ORDER BY created_at))',
        [('SELECT id FROM products ORDER BY created_at',)],
    ),
    (
        'SELECT * FROM employees WHERE id IN (SELECT employee_id FROM orders ORDER BY order_date) AND department_id IN (SELECT id FROM departments ORDER BY name)',
        [('SELECT employee_id FROM orders ORDER BY order_date',), ('SELECT id FROM departments ORDER BY name',)],
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
    'SELECT * FROM employees WHERE id IN (SELECT employee_id FROM orders WHERE amount > 100)',
    'SELECT * FROM employees WHERE id IN (SELECT employee_id FROM orders ORDER BY order_date LIMIT 5)',
])
def test_correct(query):
    result = run_test(
        query,
        detectors=[ComplicationDetector],
    )

    assert count_errors(result, ERROR) == 0
