from tests import *
import pytest

ERROR = SqlErrors.HAVING_WITHOUT_GROUP_BY


@pytest.mark.parametrize('query', [
    'SELECT * FROM store HAVING id = 1;',
    '''
        SELECT *
        FROM (
            SELECT * FROM store
            HAVING id = 1;
        ) AS sub
        ''',
    '''
        WITH cte AS (
            SELECT * FROM store
            HAVING id = 1;
        )
        SELECT * FROM cte;
        ''',
])
def test_wrong(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
        catalog_filename='miedema',
    )

    assert count_errors(detected_errors, ERROR) == 1


@pytest.mark.parametrize('query', [
    'SELECT * FROM store HAVING id = 1 GROUP BY id;',
    '''
        SELECT *
        FROM (
            SELECT * FROM store
            GROUP BY id
            HAVING id = 1;
        ) AS sub
        ''',
    '''
        WITH cte AS (
            SELECT * FROM store
            HAVING id = 1 GROUP BY id;
        )
        SELECT * FROM cte;
        ''',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
        catalog_filename='miedema',
    )

    assert count_errors(detected_errors, ERROR) == 0
