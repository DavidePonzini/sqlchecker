from tests import *
import pytest

ERROR_UNMATCHED = SqlErrors.UNMATCHED_BRACKETS
ERROR_INVALID = SqlErrors.CURLY_OR_SQUARE_BRACKETS


@pytest.mark.parametrize('query, errors', [
    (
        'SELECT * FROM orders WHERE (amount > 100;',
        [('round', 1, 0)],
    ),
    (
        'SELECT * FROM orders WHERE (amount > 100));',
        [('round', 1, 2)],
    ),
])
def test_unmatched_brackets(query, errors):
    detected_errors = run_test(
        query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR_UNMATCHED) == len(errors)
    assert count_errors(detected_errors, ERROR_INVALID) == 0
    for error in errors:
        assert has_error(detected_errors, ERROR_UNMATCHED, error)


@pytest.mark.parametrize('query, errors', [
    (
        'SELECT * FROM orders WHERE {amount > 100};',
        [('curly', 1, 1)],
    ),
    (
        'SELECT * FROM orders WHERE [amount > 100];',
        [('square', 1, 1)],
    ),
    (
        'SELECT * FROM orders WHERE amount > 100];',
        [('square', 0, 1)],
    ),
])
def test_curly_or_square_brackets(query, errors):
    detected_errors = run_test(
        query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR_UNMATCHED) == 0
    assert count_errors(detected_errors, ERROR_INVALID) == len(errors)
    for error in errors:
        assert has_error(detected_errors, ERROR_INVALID, error)


def test_mixed_brackets():
    detected_errors = run_test(
        '''
        SELECT * FROM [orders] WHERE (amount > 100] AND {status = 'shipped';
        ''',
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR_UNMATCHED) == 1
    assert count_errors(detected_errors, ERROR_INVALID) == 2
    assert has_error(detected_errors, ERROR_UNMATCHED, ('round', 1, 0))
    assert has_error(detected_errors, ERROR_INVALID, ('square', 1, 2))
    assert has_error(detected_errors, ERROR_INVALID, ('curly', 1, 0))
