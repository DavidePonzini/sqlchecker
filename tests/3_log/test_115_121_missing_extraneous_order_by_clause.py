from tests import *
import pytest


@pytest.mark.parametrize("query,solutions,schema,error", [
    (
        "SELECT cid FROM customer;",
        ["SELECT cid FROM customer ORDER BY cid;"],
        "miedema",
        SqlErrors.MISSING_ORDER_BY_CLAUSE,
    ),
    (
        "SELECT cid FROM customer ORDER BY cid;",
        ["SELECT cid FROM customer;"],
        "miedema",
        SqlErrors.EXTRANEOUS_ORDER_BY_CLAUSE,
    ),
    (
        "WITH cte AS (SELECT a FROM table1) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a FROM table1 ORDER BY a) SELECT * FROM cte;"],
        None,
        SqlErrors.MISSING_ORDER_BY_CLAUSE,
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
        "SELECT cid FROM customer ORDER BY cid;",
        ["SELECT cid FROM customer ORDER BY cid;"],
        "miedema",
    ),
    (
        "SELECT cid FROM customer;",
        ["SELECT cid FROM customer;"],
        "miedema",
    ),
    (
        "SELECT a FROM table1 ORDER BY a;",
        [],
        None,
    ),
    (
        "SELECT a FROM table1;",
        ["SELECT a FROM table1 ORDER BY a;", "SELECT a FROM table1;"],
        None,
    ),
    (
        "SELECT a FROM table1 ORDER BY a;",
        ["SELECT a FROM table1 ORDER BY a;", "SELECT a FROM table1;"],
        None,
    ),
    (
        "WITH cte AS (SELECT a FROM table1 ORDER BY a) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a, b FROM table1) SELECT a FROM cte ORDER BY b;"],
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

    assert count_errors(detected_errors, SqlErrors.MISSING_ORDER_BY_CLAUSE) == 0
    assert count_errors(detected_errors, SqlErrors.EXTRANEOUS_ORDER_BY_CLAUSE) == 0
