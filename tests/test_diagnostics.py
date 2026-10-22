import json
from zipfile import ZipFile
from sinhala_ocr.diagnostics import Diagnostics


def test_diagnostics_opt_in_and_allowlist(tmp_path):
    diagnostic = Diagnostics()
    diagnostic.record("startup")
    assert not diagnostic.events
    diagnostic.enabled = True
    diagnostic.record("private document text")
    diagnostic.record("operation_failed")
    path = tmp_path / "report.zip"
    diagnostic.export(path)
    with ZipFile(path) as archive:
        report = json.loads(archive.read("diagnostics.json"))
        assert report["events"] == ["operation_failed"]
        assert b"private document text" not in archive.read("diagnostics.json")
