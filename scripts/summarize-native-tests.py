"""Put the real native-test failure in the Actions summary, not just its status.

Only CI's synthetic test XML is read, never application/user diagnostics.
"""
import os
from pathlib import Path
import xml.etree.ElementTree as ET

report = Path('test-results/native-input.xml')
summary = os.environ.get('GITHUB_STEP_SUMMARY')
if summary and report.exists():
    root = ET.parse(report).getroot()
    with Path(summary).open('a', encoding='utf-8') as output:
        output.write('\n## Native Windows test details\n')
        for case in root.iter('testcase'):
            failures = [*case.findall('failure'), *case.findall('error')]
            if not failures:
                continue
            output.write('\n### ' + case.attrib.get('name', 'Native test') + '\n')
            for failure in failures:
                detail = (failure.text or failure.attrib.get('message', 'No detail'))[:6000]
                output.write('\n```text\n' + detail.replace('```', "'''") + '\n```\n')
