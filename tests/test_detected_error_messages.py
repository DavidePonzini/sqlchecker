import ast
from pathlib import Path
import pytest
from sqlchecker import DetectedError, SqlErrors


def test_message_is_required():
    with pytest.raises(TypeError):
        DetectedError(SqlErrors.UNDEFINED_COLUMN)


def test_message_does_not_change_error_identity():
    first = DetectedError(SqlErrors.OMITTED_SEMICOLON, message='Missing semicolon.')
    restored = DetectedError(SqlErrors.OMITTED_SEMICOLON, message='Stored explanation.')
    assert restored.message == 'Stored explanation.'
    assert first == restored
    assert hash(first) == hash(restored)


@pytest.mark.parametrize('detector', ['syntax', 'semantic', 'logical', 'complications'])
def test_every_detector_finding_provides_an_explicit_message(detector):
    import sqlchecker.detectors
    path = Path(sqlchecker.detectors.__file__).parent / f'{detector}.py'
    calls = [node for node in ast.walk(ast.parse(path.read_text()))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == 'DetectedError']
    assert calls
    for call in calls:
        assert any(keyword.arg == 'message' for keyword in call.keywords), call.lineno


@pytest.mark.parametrize('detector_name,query,solutions,error,fragment', [
    ('SyntaxErrorDetector', 'SELECT missing_column FROM store;', [], SqlErrors.UNDEFINED_COLUMN, 'missing_column'),
    ('SemanticErrorDetector', 'SELECT sid, sid FROM store;', [], SqlErrors.DUPLICATE_COLUMN_OUTPUT, 'sid'),
    ('LogicalErrorDetector', 'SELECT sid FROM store;', ['SELECT sid FROM store WHERE sid > 0;'], SqlErrors.MISSING_WHERE_CLAUSE, 'filter individual rows'),
    ('ComplicationDetector', 'WITH unused AS (SELECT sid FROM store) SELECT sid FROM store;', [], SqlErrors.UNUSED_CTE, 'never used'),
])
def test_messages_describe_actual_findings(detector_name, query, solutions, error, fragment):
    import sqlchecker
    from tests import run_test
    findings = run_test(query, catalog_filename='miedema', search_path='miedema',
                        detectors=[getattr(sqlchecker, detector_name)], solutions=solutions)
    matching = [finding for finding in findings if finding.error == error]
    assert matching
    assert all(fragment in finding.message for finding in matching)
    assert all(finding.message.strip() for finding in findings)
