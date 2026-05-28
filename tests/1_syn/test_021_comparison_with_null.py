import pytest
from tests import *

ERROR = SqlErrors.COMPARISON_WITH_NULL

OPERATORS = ['=', '<>', '<', '<=', '>', '>=']


@pytest.mark.parametrize('operator', OPERATORS)
def test_wrong(operator):
    detected_errors = run_test(
        query=f'SELECT * FROM table WHERE column {operator} NULL;',
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 1
    assert has_error(detected_errors, ERROR, (f'column {operator} NULL',))


@pytest.mark.parametrize('query, count', [
    ('SELECT * FROM table WHERE column IS NULL;', 0),
    ('SELECT * FROM table WHERE column IS NOT NULL;', 0),
    (
        '''
        SELECT * FROM table1 WHERE column1 = (
            SELECT column2 FROM table2 WHERE column3 <> NULL
        );
        ''',
        1,
    ),
])
def test_mixed(query, count):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == count
    if count:
        assert has_error(detected_errors, ERROR, ('column3 <> NULL',))
