"""Test diagnostic reporting/orchestration only, without claiming native execution."""
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('input_lab', Path(__file__).parents[1] / 'diagnostics/input_lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def test_report_preserves_mismatch_evidence(tmp_path):
    case = {'control': 'raw_rich', 'operation': 'replace', 'before': 'bad', 'after': 'වස්තුවක්',
            'inserted': 'වස්තුවක් English', 'undo_once': ' English', 'matches': False, 'qt_imported': False}
    (tmp_path / 'raw_rich.json').write_text(json.dumps({'cases': [case]}), encoding='utf-8')
    lab.summarize(tmp_path)
    report = (tmp_path / 'SUMMARY.md').read_text(encoding='utf-8')
    assert '| raw_rich | replace | bad | වස්තුවක් | NO |' in report
    assert '"undo_once": " English"' in report
    assert 'not a passing product build' in report


@pytest.mark.parametrize('failure', [None, 'exit', 'timeout'])
def test_worker_failures_stay_visible_and_other_workers_continue(tmp_path, monkeypatch, failure):
    called = []
    def run(command, **kwargs):
        kind = command[command.index('--worker') + 1]
        called.append(kind)
        if kind == 'raw_plain' and failure == 'timeout':
            raise subprocess.TimeoutExpired(command, 90)
        if kind == 'raw_plain' and failure == 'exit':
            return SimpleNamespace(returncode=3, stdout='', stderr='worker failure')
        output = Path(command[command.index('--output') + 1])
        output.write_text(json.dumps({'control': kind, 'cases': []}), encoding='utf-8')
        return SimpleNamespace(returncode=0, stdout='', stderr='')
    monkeypatch.setattr(lab.subprocess, 'run', run)
    assert lab.run_all(tmp_path) == (1 if failure else 0)
    assert called == ['raw_plain', 'raw_rich', 'qt_plain', 'app_native']
    if failure:
        assert 'worker error' in (tmp_path / 'SUMMARY.md').read_text()


def test_clipboard_probe_refuses_ordinary_computers(monkeypatch):
    monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    with pytest.raises(RuntimeError, match='disposable'):
        lab.clipboard_text(None, 'වස්තුවක්')
