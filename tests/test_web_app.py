import json
import sqlite3
import pytest
from agents.prediction import FEATURES
from web_app.app import create_app

TOKEN_A = 'a' * 64
TOKEN_B = 'b' * 64
HEADERS = {'X-Session-Token': TOKEN_A}


@pytest.fixture
def setup_app(tmp_path):
    calls = []
    def supervisor(payload):
        calls.append(payload)
        return {'safety': 'passed_limited', 'agents': {'rule': {'status':'ok', 'data': {'alerts':[], 'issues':[], 'results':[]}}, 'prediction': {'status':'ok', 'data': {'label': 1, 'probability': 0.25}}},
                'evidence':[{'source_id':'s', 'chunk_id':'c', 'text':'source', 'title':'Nguồn', 'url':'https://example.org', 'section_path':['A']}],
                'answer': {'valid':True, 'draft_status':'draft', 'text':'Thông tin [S1]', 'issues':[]}, 'disclaimer':'tham khảo'}
    path = tmp_path / 'private' / 'db.sqlite3'
    app = create_app({'TESTING':True, 'DATABASE': path, 'SUPERVISOR': supervisor})
    return app.test_client(), calls, path


def data(save=False):
    return {'features': {k: 12 for k in FEATURES}, 'measurement': {'test_type':'glucose_meter', 'unit':'mg/dL', 'value':80}, 'save_history':save}


def test_requires_local_host_session_and_safe_origin(setup_app):
    client, _, _ = setup_app
    assert client.get('/api/history').status_code == 401
    assert client.get('/api/history', headers=HEADERS | {'Origin':'https://evil.example'}).status_code == 403
    assert client.get('/api/history', headers=HEADERS | {'Host':'attacker.example'}).status_code == 403
    assert client.get('/api/history', headers=HEADERS | {'Origin':'http://localhost:bad'}).status_code == 403
    assert client.get('/api/history', headers=HEADERS).status_code == 200


def test_no_history_without_explicit_consent(setup_app):
    client, calls, path = setup_app
    response = client.post('/api/assess', json=data(), headers=HEADERS)
    assert response.status_code == 200 and response.json['result']['saved'] is False
    assert calls[0]['intent'] == 'risk' and not path.exists()
    assert client.get('/api/history', headers=HEADERS).json['history'] == []


def test_save_is_scoped_and_excludes_raw_health_data(setup_app):
    client, _, path = setup_app
    payload = data(True)
    payload['features']['Age'] = 912
    assert client.post('/api/assess', json=payload, headers=HEADERS).status_code == 200
    assert len(client.get('/api/history', headers=HEADERS).json['history']) == 1
    assert client.get('/api/history', headers={'X-Session-Token':TOKEN_B}).json['history'] == []
    with sqlite3.connect(path) as db:
        stored = db.execute('SELECT summary FROM assessments').fetchone()[0]
    assert '912' not in stored and 'features' not in stored and 'measurement' not in stored


def test_bad_inputs_do_not_call_supervisor(setup_app):
    client, calls, _ = setup_app
    payload = data()
    payload['features']['Age'] = True
    assert client.post('/api/assess', json=payload, headers=HEADERS).status_code == 400
    payload = data()
    payload['measurement']['unit'] = '%'
    assert client.post('/api/assess', json=payload, headers=HEADERS).status_code == 400
    assert client.post('/api/assess', json=data() | {'save_history':'true'}, headers=HEADERS).status_code == 400
    assert not calls


def test_chat_and_explanation_require_external_consent(setup_app):
    client, calls, _ = setup_app
    assert client.post('/api/chat', json={'question':'q','share_with_llm':False}, headers=HEADERS).status_code == 400
    assert client.post('/api/explain', json={'features':data()['features'],'measurement':data()['measurement'],'share_with_llm':False}, headers=HEADERS).status_code == 400
    assert not calls
    chat = client.post('/api/chat', json={'question':'q','share_with_llm':True}, headers=HEADERS)
    assert chat.status_code == 200 and calls[-1]['intent'] == 'knowledge'
    assert chat.json['result']['sources'][0]['citation'] == 'S1'
    assert 'text' not in chat.json['result']['sources'][0]
    explain = client.post('/api/explain', json={'features':data()['features'],'measurement':data()['measurement'],'share_with_llm':True}, headers=HEADERS)
    assert explain.status_code == 200 and calls[-1]['intent'] == 'explanation'


def test_supervisor_exception_is_not_exposed(tmp_path):
    def broken(_): raise ValueError('SECRET_HEALTH_DATA')
    client = create_app({'TESTING':True, 'DATABASE':tmp_path/'db', 'SUPERVISOR':broken}).test_client()
    response = client.post('/api/assess', json=data(), headers=HEADERS)
    assert response.status_code == 503 and 'SECRET_HEALTH_DATA' not in response.get_data(as_text=True)


def test_delete_history_only_for_current_token(setup_app):
    client, _, _ = setup_app
    assert client.post('/api/assess', json=data(True), headers=HEADERS).status_code == 200
    assert client.post('/api/assess', json=data(True), headers={'X-Session-Token':TOKEN_B}).status_code == 200
    assert client.delete('/api/history', headers=HEADERS).json['deleted'] == 1
    assert client.get('/api/history', headers=HEADERS).json['history'] == []
    assert len(client.get('/api/history', headers={'X-Session-Token':TOKEN_B}).json['history']) == 1


def test_frontend_is_served_with_security_headers(setup_app, tmp_path, monkeypatch):
    import web_app.app as app_module
    (tmp_path / 'index.html').write_text('<title>Đường nét</title>', encoding='utf-8')
    monkeypatch.setattr(app_module, 'DIST', tmp_path)
    client, _, _ = setup_app
    response = client.get('/')
    assert response.status_code == 200
    assert 'Đường nét' in response.get_data(as_text=True)
    assert response.headers['Cache-Control'] == 'no-store'
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
