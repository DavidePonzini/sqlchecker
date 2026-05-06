from tests import *
import pytest

ERROR = SqlErrors.DUPLICATE_COLUMN_OUTPUT


@pytest.mark.parametrize('query,errors', [
    (
        'SELECT street, street FROM store;',
        [('store', 'street')],
    ),
    (
        'SELECT store.street, street, sname FROM store;',
        [('store', 'street')],
    ),
    (
        'SELECT street, city FROM store WHERE store.street = store.city;',
        [('store', 'city')],
    ),
    (
        'SELECT street, city FROM store WHERE street = city;',
        [('store', 'city')],
    ),
    (
        'SELECT street, city FROM store WHERE street = sname and sname = city;',
        [('store', 'city')],
    ),
])
def test_wrong(query, errors):
    result = run_test(
        query,
        detectors=[SemanticErrorDetector],
        catalog_filename='miedema',
        search_path='miedema'
    )

    assert count_errors(result, ERROR) == len(errors)
    for error in errors:
        assert has_error(result, ERROR, error)


@pytest.mark.parametrize('query', [
    'SELECT street, city FROM store;',
    'SELECT street, 1 FROM store;',
    'SELECT street, 1, 1 FROM store;',
    'SELECT street, city FROM store WHERE street > city;',
    'SELECT street, city FROM store WHERE street = city + 1;',
    'SELECT sid, sid+1 FROM store;',
])
def test_correct(query):
    result = run_test(
        query,
        detectors=[SemanticErrorDetector],
        catalog_filename='miedema',
        search_path='miedema'
    )

    assert count_errors(result, ERROR) == 0
