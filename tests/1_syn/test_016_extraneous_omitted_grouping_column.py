from tests import *
import pytest

ERROR = SqlErrors.EXTRANEOUS_OR_OMITTED_GROUPING_COLUMN

@pytest.mark.parametrize('query', [
    'SELECT id, sum(col2) FROM store GROUP BY id',
    '''
        SELECT                                                 
            c.full_name,
            COUNT(t.trans_key) AS total_transactions,
            (
                SELECT AVG(t2.amount)
                FROM transactions t2
                JOIN accounts a2 ON a2.acc_key = t2.related_account
                WHERE a2.balance > 1000
                    AND a2.acc_type = 'Savings'
            ) AS average_transaction_amount
        FROM customers c
        JOIN accounts a ON a.ref_customer = c.cust_id
        JOIN transactions t ON t.related_account = a.acc_key
        WHERE c.full_name LIKE 'Smith___%'
        GROUP BY c.full_name;
    ''',
    'SELECT id, sum(col2) FROM store GROUP BY id, col2',

])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 0

@pytest.mark.parametrize('query, errors', [
    (
        'SELECT id, SUM(col2) FROM store GROUP BY 1, 2',
        [('col2', 'AGGREGATED IN GROUP BY')],
    ),
    (
        'SELECT id, SUM(col2) FROM store GROUP BY id, SUM(col2)',
        [('col2', 'AGGREGATED IN GROUP BY')],
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
