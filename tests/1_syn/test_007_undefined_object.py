from tests import *
import pytest

ERROR = SqlErrors.UNDEFINED_OBJECT

@pytest.mark.parametrize('query,objects,schema', [
    ('SELECT * FROM store;', ('store',), None),
    ('SELECT * FROM customer c JOIN orders o ON c.cid = o.cid;', ['orders AS o'], 'miedema'),
    # subqueries
    ('SELECT * FROM products p WHERE p.pid IN (SELECT pid FROM my_table);', ['products AS p', 'my_table'], 'miedema'),
    # CTEs
    ('WITH temp AS (SELECT * FROM employees) SELECT * FROM temp;', ['employees'], None),
    ('WITH temp AS (SELECT * FROM unknown_table) SELECT * FROM temp2 WHERE id > 5;', ['unknown_table', 'temp2'], None),
])
def test_wrong(query, objects, schema):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
        catalog_filename=schema,
        search_path=schema,
    )

    assert count_errors(detected_errors, ERROR) == len(objects)
    for obj in objects:
        assert has_error(detected_errors, ERROR, (obj,))

@pytest.mark.parametrize('query,schema', [
    ('SELECT * FROM store;', 'miedema'),
    ('SELECT * FROM customer c JOIN store s ON c.cid = s.sid;', 'miedema'),
    # subqueries
    ('SELECT * FROM customer c WHERE c.sid IN (SELECT sid FROM store);', 'miedema'),
    ('''SELECT customers.full_name,
            loan_totals.total_loan_amount,
            account_totals.total_balance
    FROM customers
    JOIN (
        SELECT borrower_id, SUM(amount) AS total_loan_amount
        FROM loans
        GROUP BY borrower_id
    ) AS loan_totals
    ON loan_totals.borrower_id = customers.cust_id
    JOIN (
        SELECT ref_customer, SUM(balance) AS total_balance
        FROM accounts
        GROUP BY ref_customer
    ) AS account_totals
    ON account_totals.ref_customer = customers.cust_id
    WHERE loan_totals.total_loan_amount > 5000
    AND account_totals.total_balance > (
        SELECT AVG(balance)
        FROM accounts
    );''', 'gen1'),
    # CTEs
    ('WITH temp AS (SELECT * FROM store) SELECT * FROM temp;', 'miedema'),
])
def test_correct(query, schema):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
        catalog_filename=schema,
        search_path=schema,
    )

    assert count_errors(detected_errors, ERROR) == 0
