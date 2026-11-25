from unittest.mock import patch
from pathlib import Path

from agents.settings import GEMINI_ENDPOINT, GEMINI_MODEL, llm_settings
from agents.reasoning import ReasoningAgent


def test_read_dotenv_without_printing_secret(monkeypatch):
    for key in ('RAG_LLM_ENDPOINT', 'RAG_LLM_MODEL', 'RAG_LLM_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY'):
        monkeypatch.delenv(key, raising=False)
    with patch.object(Path, 'exists', return_value=True), patch.object(Path, 'read_text', return_value='NEO4J_PASSWORD=ignore\nRAG_LLM_API_KEY="test-secret"\n'):
        result = llm_settings(Path('irrelevant'))
    assert result == {'endpoint': GEMINI_ENDPOINT, 'model': GEMINI_MODEL, 'api_key': 'test-secret'}


def test_environment_precedes_file(monkeypatch):
    monkeypatch.setenv('RAG_LLM_API_KEY', 'env-secret')
    monkeypatch.setenv('RAG_LLM_MODEL', 'custom-model')
    with patch.object(Path, 'exists', return_value=True), patch.object(Path, 'read_text', return_value='RAG_LLM_API_KEY=file-secret'):
        result = llm_settings(Path('irrelevant'))
    assert result['api_key'] == 'env-secret' and result['model'] == 'custom-model'


def test_reasoning_uses_settings_without_disclosing_key():
    settings = {'endpoint': GEMINI_ENDPOINT, 'model': GEMINI_MODEL, 'api_key': 'secret'}
    with patch('agents.reasoning.llm_settings', return_value=settings):
        agent = ReasoningAgent(answer_fn=lambda *args: 'Dựa vào tài liệu [S1]')
        result = agent.run('Câu hỏi', [{'text': 'bằng chứng'}])
    assert result['status'] == 'draft' and 'secret' not in str(result)


def test_gemini_request_uses_low_reasoning_effort():
    import json
    from rag.core import answer
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, *args): return json.dumps({'choices': [{'message': {'content': 'Thông tin [S1]'}}]}).encode()
    evidence = [{'chunk_id': 'c', 'source_id': 's', 'text': 'source'}]
    with patch('rag.core.urlopen', return_value=Response()) as call:
        assert answer('q', evidence, GEMINI_ENDPOINT, GEMINI_MODEL, 'secret') == 'Thông tin [S1]'
    assert json.loads(call.call_args.args[0].data)['reasoning_effort'] == 'low'
