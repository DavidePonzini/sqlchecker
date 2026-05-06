from tests import *
import pytest

ERROR = SqlErrors.CONSTANT_COLUMN_OUTPUT


@pytest.mark.xfail(reason='Not implemented yet')
@pytest.mark.parametrize('query,errors', [
    (
        'SELECT a FROM orders WHERE a = 1;',
        [('a',)],
    ),
])
def test_wrong(query, errors):
    result = run_test(
        query,
        detectors=[SemanticErrorDetector],
    )

    assert count_errors(result, ERROR) == len(errors)
    for error in errors:
        assert has_error(result, ERROR, error)

@pytest.mark.xfail(reason='Not implemented yet')
@pytest.mark.parametrize('query', [
    'SELECT a FROM orders;',
    'SELECT a, b FROM orders WHERE a = b;',
    'SELECT 1 FROM orders;',
])
def test_correct(query):
    result = run_test(
        query,
        detectors=[SemanticErrorDetector],
    )

    assert count_errors(result, ERROR) == 0
