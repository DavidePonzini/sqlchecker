from tests import *
import pytest


@pytest.mark.parametrize("query,solutions,schema,error", [
    (
        "SELECT city, COUNT(*) FROM customer;",
        ["SELECT city, COUNT(*) FROM customer GROUP BY city;"],
        "miedema",
        SqlErrors.MISSING_GROUP_BY_CLAUSE,
    ),
    (
        "SELECT city, COUNT(*) FROM customer GROUP BY city;",
        ["SELECT city, COUNT(*) FROM customer;"],
        "miedema",
        SqlErrors.EXTRANEOUS_GROUP_BY_CLAUSE,
    ),
    (
        "WITH cte AS (SELECT a, COUNT(*) FROM table1) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a, COUNT(*) FROM table1 GROUP BY a) SELECT * FROM cte;"],
        None,
        SqlErrors.MISSING_GROUP_BY_CLAUSE,
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
        "SELECT city, COUNT(*) FROM customer GROUP BY city;",
        ["SELECT city, COUNT(*) FROM customer GROUP BY city;"],
        "miedema",
    ),
    (
        "SELECT COUNT(*) FROM customer;",
        ["SELECT COUNT(*) FROM customer;"],
        "miedema",
    ),
    (
        "SELECT a, COUNT(*) FROM table1 GROUP BY a;",
        [],
        None,
    ),
    (
        "SELECT COUNT(*) FROM table1;",
        ["SELECT a, COUNT(*) FROM table1 GROUP BY a;", "SELECT COUNT(*) FROM table1;"],
        None,
    ),
    (
        "WITH cte AS (SELECT a, COUNT(*) FROM table1 GROUP BY a) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a, b FROM table1) SELECT a, COUNT(*) FROM cte GROUP BY a;"],
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

    assert count_errors(detected_errors, SqlErrors.MISSING_GROUP_BY_CLAUSE) == 0
    assert count_errors(detected_errors, SqlErrors.EXTRANEOUS_GROUP_BY_CLAUSE) == 0
