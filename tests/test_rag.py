import json
from unittest.mock import patch

import pytest
from rag.core import ABSTAIN, answer, context, fuse, match_entities, subchunks


def test_subchunks_keep_offsets_and_cover_text():
    class Tokenizer:
        def __call__(self, text, **kwargs):
            return {'offset_mapping': [(i, i + 1) for i in range(len(text))]}
    chunks = list(subchunks([{'id': 'c', 'text': 'abcdefghij'}], Tokenizer(), 4, 1))
    assert [(c['start'], c['end'], c['text']) for c in chunks] == [(0, 4, 'abcd'), (3, 7, 'defg'), (6, 10, 'ghij')]
    assert len({c['id'] for c in chunks}) == 3


def test_entities_match_word_boundaries_and_case():
    entities = [{'id': 'x', 'aliases': ['insulin']}, {'id': 'y', 'aliases': ['đường huyết']}]
    assert match_entities('INSULIN và đường huyết', entities) == ['x', 'y']
    assert match_entities('hyperinsulin', entities) == []


def test_fusion_deduplicates_parent_and_reinforces_both_channels():
    vector = [{'chunk_id': 'a', 'text': 'a'}, {'chunk_id': 'a', 'text': 'a2'}, {'chunk_id': 'b', 'text': 'b'}]
    graph = [{'chunk_id': 'b', 'text': 'b'}, {'chunk_id': 'b', 'text': 'b2'}]
    results = fuse(vector, graph)
    assert [r['chunk_id'] for r in results] == ['b', 'a']
    assert results[0]['channels'] == ['vector', 'kg']


def test_answer_rejects_missing_or_invalid_citation():
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, *args): return json.dumps({'choices': [{'message': {'content': 'Kết luận [S9]'}}]}).encode()
    record = {'chunk_id': 'c', 'source_id': 's', 'text': 'test', 'source_path': 'local'}
    assert '[S1]' in context([record])
    assert answer('q', [], 'http://example.test', 'model') == ABSTAIN
    with patch('rag.core.urlopen', return_value=Response()):
        assert answer('q', [record], 'http://example.test', 'model') == ABSTAIN


def test_answer_sends_evidence_and_preserves_valid_citation():
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, *args): return json.dumps({'choices': [{'message': {'content': 'Thông tin [S1]'}}]}).encode()
    record = {'chunk_id': 'c', 'source_id': 's', 'text': 'Nội dung nguồn', 'source_path': 'local'}
    with patch('rag.core.urlopen', return_value=Response()) as send:
        assert answer('Câu hỏi', [record], 'http://example.test', 'model') == 'Thông tin [S1]'
        payload = json.loads(send.call_args.args[0].data)
        assert 'Nội dung nguồn' in payload['messages'][0]['content']
        assert 'local' in payload['messages'][0]['content']
