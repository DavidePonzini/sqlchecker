from tests import *
import pytest


@pytest.mark.parametrize("query,solutions,schema,error", [
    (
        "SELECT cid FROM customer;",
        ["SELECT cid FROM customer WHERE city = 'Rome';"],
        "miedema",
        SqlErrors.MISSING_WHERE_CLAUSE,
    ),
    (
        "SELECT cid FROM customer WHERE city = 'Rome';",
        ["SELECT cid FROM customer;"],
        "miedema",
        SqlErrors.EXTRANEOUS_WHERE_CLAUSE,
    ),
    (
        "WITH cte AS (SELECT a FROM table1) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a FROM table1 WHERE b = 1) SELECT * FROM cte;"],
        None,
        SqlErrors.MISSING_WHERE_CLAUSE,
    ),
])
def test_wrong(query, solutions, schema, error):
    detected_errors = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
        catalog_filename=schema,
        search_path=schema,
    )

    assert count_errors(detected_errors, error) == 1


@pytest.mark.parametrize("query,solutions,schema", [
    (
        "SELECT cid FROM customer WHERE city = 'Rome';",
        ["SELECT cid FROM customer WHERE city = 'Rome';"],
        "miedema",
    ),
    (
        "SELECT cid FROM customer;",
        ["SELECT cid FROM customer;"],
        "miedema",
    ),
    (
        "SELECT a FROM table1 WHERE b = 1;",
        [],
        None,
    ),
    (
        "SELECT a FROM table1;",
        ["SELECT a FROM table1 WHERE b = 1;", "SELECT a FROM table1;"],
        None,
    ),
    (
        "WITH cte AS (SELECT a FROM table1 WHERE b = 1) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a, b FROM table1) SELECT a FROM cte WHERE b = 1;"],
        None,
    )
])
def test_correct(query, solutions, schema):
    detected_errors = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
        catalog_filename=schema,
        search_path=schema,
    )

    assert count_errors(detected_errors, SqlErrors.MISSING_WHERE_CLAUSE) == 0
    assert count_errors(detected_errors, SqlErrors.EXTRANEOUS_WHERE_CLAUSE) == 0
