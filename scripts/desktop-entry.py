import sys

try:
    from sinhala_ocr.app import main
    result = main()
except Exception as error:
    if '--smoke-test' in sys.argv:
        # Standard-library reporting still works if an application import fails.
        import json
        from pathlib import Path
        import traceback
        Path('packaged-smoke.json').write_text(json.dumps({
            'status': 'failed', 'stage': 'startup', 'error_type': type(error).__name__,
            'error': str(error)[:4000], 'traceback': traceback.format_exc(limit=8)[-8000:]
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        result = 1
    else:
        raise
raise SystemExit(result)
