import json

import pytest

from sinhala_ocr.word_memory import WordMemory


def test_words_persist_exactly_and_suggest_without_rewriting(tmp_path):
    path = tmp_path / 'words.json'
    memory = WordMemory(path)
    for word in ['වස්තුවක්', 'ශ්‍රී', 'වවවව', 'x²', 'සිංහල වචන']:
        memory.add(word)
    memory.add('වස්තුවක්')
    loaded = WordMemory(path)
    assert loaded.words == ['වස්තුවක්', 'ශ්‍රී', 'වවවව', 'x²', 'සිංහල වචන']
    before = path.read_bytes()
    assert 'වස්තුවක්' in loaded.suggestions('වස්තු')
    assert path.read_bytes() == before
    loaded.remove('වවවව')
    assert 'වවවව' not in WordMemory(path).words


@pytest.mark.parametrize('data', [[], {'version': 3, 'words': []}, {'version': 1, 'words': ['bad\nword']}, {'version': 1, 'words': [1]}])
def test_corrupt_vocabulary_is_not_overwritten(tmp_path, data):
    path = tmp_path / 'words.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    before = path.read_bytes()
    with pytest.raises(ValueError):
        WordMemory(path)
    assert path.read_bytes() == before


def test_failed_save_keeps_previous_words(tmp_path, monkeypatch):
    memory = WordMemory(tmp_path / 'words.json')
    memory.add('වස්තුවක්')
    from sinhala_ocr import word_memory
    def fail(*args):
        raise OSError('disk full')
    monkeypatch.setattr(word_memory, 'atomic_write', fail)
    with pytest.raises(OSError):
        memory.add('සිංහල')
    assert memory.words == ['වස්තුවක්']
    assert WordMemory(memory.path).words == memory.words
