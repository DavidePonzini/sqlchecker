from tests import *
import pytest


@pytest.mark.parametrize("query,solutions,schema,error,data", [
    (
        "SELECT cid FROM customer;",
        ["SELECT cid FROM customer LIMIT 5;"],
        "miedema",
        SqlErrors.MISSING_LIMIT_CLAUSE,
        (),
    ),
    (
        "SELECT cid FROM customer LIMIT 5;",
        ["SELECT cid FROM customer;"],
        "miedema",
        SqlErrors.EXTRANEOUS_LIMIT_CLAUSE,
        (),
    ),
    (
        "SELECT cid FROM customer LIMIT 10;",
        ["SELECT cid FROM customer LIMIT 5;"],
        "miedema",
        SqlErrors.INCORRECT_LIMIT,
        ({10}, {5}),
    ),
])
def test_wrong(query, solutions, schema, error, data):
    detected_errors = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
        catalog_filename=schema,
        search_path=schema,
    )

    assert count_errors(detected_errors, error) == 1
    if data:
        assert has_error(detected_errors, error, data)


@pytest.mark.parametrize("query,solutions,schema", [
    (
        "SELECT cid FROM customer LIMIT 5;",
        ["SELECT cid FROM customer LIMIT 5;"],
        "miedema",
    ),
    (
        "SELECT cid FROM customer;",
        ["SELECT cid FROM customer;"],
        "miedema",
    ),
    (
        "SELECT a FROM table1 LIMIT 5;",
        [],
        None,
    ),
    (
        "SELECT a FROM table1;",
        ["SELECT a FROM table1 LIMIT 5;", "SELECT a FROM table1;"],
        None,
    ),
    (
        "SELECT * FROM (SELECT a FROM table1 LIMIT 5) AS t;",
        ["SELECT * FROM (SELECT a FROM table1) AS t;"],
        None,
    ),
])
def test_correct(query, solutions, schema):
    detected_errors = run_test(
        query,
        solutions=solutions,
        detectors=[LogicalErrorDetector],
        catalog_filename=schema,
        search_path=schema,
    )

    assert count_errors(detected_errors, SqlErrors.MISSING_LIMIT_CLAUSE) == 0
    assert count_errors(detected_errors, SqlErrors.EXTRANEOUS_LIMIT_CLAUSE) == 0
    assert count_errors(detected_errors, SqlErrors.INCORRECT_LIMIT) == 0
