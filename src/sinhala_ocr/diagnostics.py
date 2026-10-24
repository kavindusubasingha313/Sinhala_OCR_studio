"""Opt-in, allowlisted event diagnostics; never capture documents or exception text."""
import json
import platform
from collections import deque
from zipfile import ZipFile

from . import __version__
from .core import atomic_write


class Diagnostics:
    def __init__(self):
        self.enabled = False
        self.events = deque(maxlen=200)

    def record(self, event):
        if self.enabled and event in {"startup", "operation_failed", "export_report", "smoke_passed"}:
            self.events.append(event)

    def export(self, path):
        report = {"application": "Sinhala OCR Studio", "version": __version__,
                  "os": platform.system(), "os_release": platform.release(),
                  "python": platform.python_version(), "diagnostics_enabled": self.enabled,
                  "events": list(self.events)}
        def write(temporary):
            with ZipFile(temporary, "w") as archive:
                archive.writestr("diagnostics.json", json.dumps(report, indent=2))
                archive.writestr("README.txt", "No document text, source paths, environment variables or credentials are included. Add reproduction steps and only redacted screenshots yourself.")
        def validate(temporary):
            with ZipFile(temporary) as archive:
                json.loads(archive.read("diagnostics.json"))
        atomic_write(path, write, validate)
