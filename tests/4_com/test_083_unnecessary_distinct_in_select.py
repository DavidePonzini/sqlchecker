import pytest
from tests import *

ERROR = SqlErrors.UNNECESSARY_DISTINCT_IN_SELECT_CLAUSE


@pytest.mark.parametrize('query, errors', [
    (
        'SELECT DISTINCT cid, cname FROM customer',
        [('SELECT DISTINCT cid, cname FROM customer',)],
    ),
])
def test_wrong(query, errors):
    result = run_test(
        query,
        search_path='miedema',
        catalog_filename='miedema',
        detectors=[ComplicationDetector],
    )

    assert count_errors(result, ERROR) == len(errors)
    for error in errors:
        assert has_error(result, ERROR, error)


@pytest.mark.parametrize('query', [
    'SELECT DISTINCT c1.cid, c1.cname FROM customer c1 JOIN customer c2 ON c1.cid <> c2.cid',
    'SELECT DISTINCT street FROM customer',
])
def test_correct(query):
    result = run_test(
        query,
        search_path='miedema',
        catalog_filename='miedema',
        detectors=[ComplicationDetector],
    )

    assert count_errors(result, ERROR) == 0
