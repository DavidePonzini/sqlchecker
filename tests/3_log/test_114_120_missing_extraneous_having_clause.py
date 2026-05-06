from tests import *
import pytest


@pytest.mark.parametrize("query,solutions,schema,error", [
    (
        "SELECT city, COUNT(*) FROM customer GROUP BY city;",
        ["SELECT city, COUNT(*) FROM customer GROUP BY city HAVING COUNT(*) > 1;"],
        "miedema",
        SqlErrors.MISSING_HAVING_CLAUSE,
    ),
    (
        "SELECT city, COUNT(*) FROM customer GROUP BY city HAVING COUNT(*) > 1;",
        ["SELECT city, COUNT(*) FROM customer GROUP BY city;"],
        "miedema",
        SqlErrors.EXTRANEOUS_HAVING_CLAUSE,
    ),
    (
        "WITH cte AS (SELECT a, COUNT(*) FROM table1 GROUP BY a) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a, COUNT(*) FROM table1 GROUP BY a HAVING COUNT(*) > 1) SELECT * FROM cte;"],
        None,
        SqlErrors.MISSING_HAVING_CLAUSE,
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
        "SELECT city, COUNT(*) FROM customer GROUP BY city HAVING COUNT(*) > 1;",
        ["SELECT city, COUNT(*) FROM customer GROUP BY city HAVING COUNT(*) > 1;"],
        "miedema",
    ),
    (
        "SELECT city, COUNT(*) FROM customer GROUP BY city;",
        ["SELECT city, COUNT(*) FROM customer GROUP BY city;"],
        "miedema",
    ),
    (
        "SELECT a, COUNT(*) FROM table1 GROUP BY a HAVING COUNT(*) > 1;",
        [],
        None,
    ),
    (
        "SELECT a, COUNT(*) FROM table1 GROUP BY a;",
        [
            "SELECT a, COUNT(*) FROM table1 GROUP BY a HAVING COUNT(*) > 1;",
            "SELECT a, COUNT(*) FROM table1 GROUP BY a;",
        ],
        None,
    ),
    (
        "WITH cte AS (SELECT a, COUNT(*) FROM table1 GROUP BY a HAVING COUNT(*) > 1) SELECT * FROM cte;",
        ["WITH cte AS (SELECT a, b FROM table1) SELECT a, COUNT(*) FROM cte GROUP BY a HAVING COUNT(*) > 1;"],
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

    assert count_errors(detected_errors, SqlErrors.MISSING_HAVING_CLAUSE) == 0
    assert count_errors(detected_errors, SqlErrors.EXTRANEOUS_HAVING_CLAUSE) == 0
