import json
from io import BytesIO

from PIL import Image
import pytest

from sinhala_ocr.advanced_ocr import AdvancedOcrError, CredentialStore, recognize_with_ai


def png():
    output = BytesIO()
    Image.new("RGB", (20, 20), "white").save(output, "PNG")
    return output.getvalue()


def response(text, equations=None):
    return {"status": "completed", "output": [{"content": [{"type": "output_text", "text": json.dumps({"text": text, "equations": equations or []})}]}], "usage": {"input_tokens": 100, "output_tokens": 20}}


def test_no_consent_means_no_upload():
    def forbidden(*args):
        pytest.fail("No network call is allowed without consent")
    with pytest.raises(AdvancedOcrError, match="consent"):
        recognize_with_ai(png(), consent=False, api_key="test", transport=forbidden)


def test_ai_page_payload_and_editable_equation_mapping():
    calls = []
    def transport(payload, key):
        calls.append(payload)
        return response("සිංහල [[equation:1]]", [{"latex": r"E=\frac{1}{2}mv^2", "placement": "inline"}])
    result = recognize_with_ai(png(), consent=True, api_key="test", latex_enabled=True, transport=transport)
    assert len(calls) == 1
    assert calls[0]["store"] is False
    assert calls[0]["max_output_tokens"] == 4096
    assert len(calls[0]["input"][0]["content"]) == 1
    assert "test" not in json.dumps(calls[0])
    assert result.equations[0].marker in result.text
    assert result.equations[0].original_latex == r"E=\frac{1}{2}mv^2"
    assert result.equations[0].status == "draft"
    assert result.input_tokens == 100


def test_off_rejects_unrequested_equation_output():
    with pytest.raises(AdvancedOcrError, match="OFF"):
        recognize_with_ai(png(), consent=True, api_key="test", transport=lambda *_: response("[[equation:1]]", [{"latex": "x", "placement": "display"}]))


@pytest.mark.parametrize("bad", [{"status": "incomplete"}, response("[[equation:1]]"), response("no marker", [{"latex": "x", "placement": "inline"}]), {"status": "completed", "output": None}])
def test_invalid_ai_result_is_not_accepted(bad):
    with pytest.raises(AdvancedOcrError):
        recognize_with_ai(png(), consent=True, api_key="test", latex_enabled=True, transport=lambda *_: bad)


def test_plaintext_keyring_is_rejected(monkeypatch):
    import keyring
    class InsecureBackend:
        pass
    monkeypatch.setattr(keyring, "get_keyring", lambda: InsecureBackend())
    with pytest.raises(AdvancedOcrError, match="OS-backed"):
        CredentialStore().save("example-key")
