import pytest
from tests import *

ERROR = SqlErrors.NONSTANDARD_OPERATORS

NONSTANDARD_OPS = {
    '==': '=',
    '===': '=',
    '!==': '<>',
    '&&': ' AND ',
    '||': ' OR ',
    '!': ' NOT ',
    '>>': '>',
    '<<': '<',
    '≠': '<>',
    '≥': '>=',
    '≤': '<=',
}


@pytest.mark.parametrize('op,expected', NONSTANDARD_OPS.items())
def test_nonstandard_operator(op: str, expected: str):
    query = f'SELECT * FROM users WHERE age {op} 30;'

    detected_errors = run_test(
        query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR) == 1
    assert has_error(detected_errors, ERROR, (op, expected))
