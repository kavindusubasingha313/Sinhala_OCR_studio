"""Progress/failure reporting for the explicitly requested synthetic smoke test."""
import json
from pathlib import Path
import traceback


class SmokeReport:
    def __init__(self, path='packaged-smoke.json'):
        self.path = Path(path)
        self.data = {'status': 'running', 'stage': 'startup', 'completed_stages': []}
        self.write()

    def write(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')

    def phase(self, name):
        if self.data['stage'] != 'startup':
            self.data['completed_stages'].append(self.data['stage'])
        self.data['stage'] = name
        self.write()

    def check(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def finish(self):
        self.data['completed_stages'].append(self.data['stage'])
        self.data['status'] = 'passed'
        self.write()

    def fail(self, error):
        self.data.update(status='failed', error_type=type(error).__name__,
                         error=str(error)[:4000], traceback=traceback.format_exc(limit=8)[-8000:])
        self.write()
