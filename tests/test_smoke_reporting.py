import json
from types import SimpleNamespace

from sinhala_ocr.smoke_report import SmokeReport


def test_checkpoints_preserve_last_stage_and_failure(tmp_path):
    path = tmp_path / 'report.json'
    report = SmokeReport(path)
    report.phase('offline_ocr')
    report.phase('native_typing_pad')
    assert json.loads(path.read_text())['completed_stages'] == ['offline_ocr']
    try:
        report.check(False, 'synthetic expected/actual mismatch')
    except AssertionError as error:
        report.fail(error)
    data = json.loads(path.read_text())
    assert data['stage'] == 'native_typing_pad'
    assert data['status'] == 'failed'
    assert data['error'] == 'synthetic expected/actual mismatch'
    assert 'AssertionError' in data['traceback']


def test_smoke_failure_identifies_stage_and_returns_failure(tmp_path, monkeypatch):
    from sinhala_ocr import app
    monkeypatch.chdir(tmp_path)
    def fail(self, image):
        raise RuntimeError('synthetic missing OCR runtime')
    monkeypatch.setattr(app.TesseractEngine, 'recognize', fail)
    codes = []
    app.smoke_test(SimpleNamespace(exit=codes.append), None)
    data = json.loads((tmp_path / 'packaged-smoke.json').read_text())
    assert codes == [1]
    assert data['stage'] == 'offline_ocr'
    assert data['status'] == 'failed'
    assert data['error'] == 'synthetic missing OCR runtime'


def test_success_requires_explicit_finish(tmp_path):
    path = tmp_path / 'report.json'
    report = SmokeReport(path)
    report.phase('docx_export')
    assert json.loads(path.read_text())['status'] == 'running'
    report.finish()
    data = json.loads(path.read_text())
    assert data['status'] == 'passed'
    assert data['completed_stages'] == ['docx_export']
