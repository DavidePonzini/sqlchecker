from tests import *
import pytest

ERROR_ADDITIONAL = SqlErrors.ADDITIONAL_SEMICOLON
ERROR_OMITTED = SqlErrors.OMITTED_SEMICOLON


@pytest.mark.parametrize('query, additional_count, omitted_count', [
    (
        '''
        SELECT column1, column2 FROM table1;;
        ''',
        1,
        0,
    ),
    (
        '''
        SELECT column1, column2; FROM table1
        ''',
        1,
        1,
    ),
    (
        '''
        ;SELECT column1, column2 FROM table1;
        ''',
        1,
        0,
    ),
    (
        '''
        SELECT column1, column2 FROM table1
        ''',
        0,
        1,
    ),
])
def test_wrong(query, additional_count, omitted_count):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR_ADDITIONAL) == additional_count
    assert count_errors(detected_errors, ERROR_OMITTED) == omitted_count


@pytest.mark.parametrize('query', [
    '''
        SELECT column1, column2 FROM table1;
        ''',
])
def test_correct(query):
    detected_errors = run_test(
        query=query,
        detectors=[SyntaxErrorDetector],
    )

    assert count_errors(detected_errors, ERROR_ADDITIONAL) == 0
    assert count_errors(detected_errors, ERROR_OMITTED) == 0
