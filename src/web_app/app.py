from __future__ import annotations

import hashlib
import json
import math
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, jsonify, request, send_from_directory
from agents.coordinator import CoordinatorAgent
from agents.prediction import FEATURES

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'frontend' / 'dist'
DB_PATH = ROOT / 'data' / 'private' / 'history.sqlite3'
FIELDS = {'test_type', 'value', 'unit', 'pregnant', 'sample', 'fasting_hours', 'glucose_load_g', 'elapsed_minutes', 'lab_certified', 'a1c_interference'}


def token_hash(token):
    if not isinstance(token, str) or len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
        return None
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS assessments (id TEXT PRIMARY KEY, owner TEXT NOT NULL, created_at TEXT NOT NULL, summary TEXT NOT NULL)')
    return db


def summary_for_history(result):
    agents = result.get('agents', {})
    prediction = agents.get('prediction', {})
    data = prediction.get('data') or {}
    rule = agents.get('rule', {}).get('data') or {}
    return {'safety': result.get('safety'), 'prediction_status': prediction.get('status'),
            'label': data.get('label'), 'probability': data.get('probability'),
            'alerts': [{'rule_id': x.get('rule_id'), 'message': x.get('message')} for x in rule.get('alerts', [])],
            'issues': [{'code': x.get('code'), 'field': x.get('field')} for x in rule.get('issues', [])]}


def safe_sources(result):
    sources = []
    for i, row in enumerate(result.get('evidence', []), 1):
        url = row.get('url')
        try:
            valid_url = isinstance(url, str) and urlsplit(url).scheme in ('http', 'https') and bool(urlsplit(url).hostname)
        except ValueError:
            valid_url = False
        if not valid_url:
            url = None
        sources.append({'citation': f'S{i}', 'title': row.get('title') or 'Tài liệu', 'url': url,
                        'source_path': row.get('source_path'), 'chunk_id': row.get('chunk_id'),
                        'section_path': row.get('section_path') or []})
    return sources


def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(MAX_CONTENT_LENGTH=32768, DATABASE=DB_PATH, SUPERVISOR=None)
    if config:
        app.config.update(config)

    @app.before_request
    def protect_local_access():
        if not request.path.startswith('/api/'):
            return None
        host = request.host.split(':')[0].lower()
        if host not in {'localhost', '127.0.0.1'}:
            return jsonify(error='host_not_allowed'), 403
        origin = request.headers.get('Origin')
        if origin:
            try:
                parsed = urlsplit(origin)
                allowed = parsed.scheme == 'http' and parsed.hostname in {'localhost', '127.0.0.1'} and parsed.port in {5000, 5173} and not parsed.username and not parsed.password
            except ValueError:
                allowed = False
            if not allowed:
                return jsonify(error='origin_not_allowed'), 403
        if not token_hash(request.headers.get('X-Session-Token')):
            return jsonify(error='invalid_session'), 401
        if request.method == 'POST' and not request.is_json:
            return jsonify(error='json_required'), 415
        return None

    @app.after_request
    def security_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
        return response

    def run_supervisor(payload):
        return app.config['SUPERVISOR'](payload) if app.config['SUPERVISOR'] else CoordinatorAgent().supervise(payload)

    def body():
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else None

    def finite_number(value, allow_zero=True):
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and (value >= 0 if allow_zero else value > 0)

    def validate_inputs(features, measurement):
        if not isinstance(features, dict) or set(features) != set(FEATURES) or any(not finite_number(v) for v in features.values()):
            return 'invalid_features'
        if (not isinstance(measurement, dict) or set(measurement) - FIELDS or measurement.get('test_type') not in {'glucose_meter', 'glucose_random', 'fpg', 'ogtt_2h', 'hba1c'}
                or not finite_number(measurement.get('value'), False) or measurement.get('unit') != ('%' if measurement.get('test_type') == 'hba1c' else 'mg/dL')):
            return 'invalid_measurement'
        return None

    def answer_payload(result):
        answer = result.get('answer') or {}
        return {'answer': answer.get('text'), 'valid': answer.get('valid', False),
                'status': answer.get('draft_status') or 'unavailable', 'issues': answer.get('issues', []),
                'sources': safe_sources(result), 'disclaimer': result.get('disclaimer')}

    @app.post('/api/assess')
    def assess():
        data = body()
        if data is None or set(data) != {'features', 'measurement', 'save_history'} or type(data['save_history']) is not bool:
            return jsonify(error='invalid_request'), 400
        features, measurement = data['features'], data['measurement']
        problem = validate_inputs(features, measurement)
        if problem:
            return jsonify(error=problem), 400
        try:
            result = run_supervisor({'intent': 'risk', 'features': features, 'measurement': measurement})
            record = summary_for_history(result)
            if data['save_history']:
                owner = token_hash(request.headers['X-Session-Token'])
                with database(Path(app.config['DATABASE'])) as db:
                    db.execute('INSERT INTO assessments VALUES (?, ?, ?, ?)', (secrets.token_hex(16), owner, datetime.now(timezone.utc).isoformat(), json.dumps(record, ensure_ascii=False)))
            return jsonify(result={'summary': record, 'disclaimer': result.get('disclaimer'), 'saved': data['save_history']})
        except Exception:
            return jsonify(error='assessment_unavailable'), 503

    @app.post('/api/chat')
    def chat():
        data = body()
        if data is None or set(data) != {'question', 'share_with_llm'} or type(data['share_with_llm']) is not bool:
            return jsonify(error='invalid_request'), 400
        question = data['question']
        if not isinstance(question, str) or not question.strip() or len(question) > 1000:
            return jsonify(error='invalid_question'), 400
        if not data['share_with_llm']:
            return jsonify(error='llm_consent_required'), 400
        try:
            result = run_supervisor({'intent': 'knowledge', 'question': question.strip(), 'generate_answer': True})
            return jsonify(result=answer_payload(result))
        except Exception:
            return jsonify(error='chat_unavailable'), 503

    @app.post('/api/explain')
    def explain():
        data = body()
        if data is None or set(data) != {'features', 'measurement', 'share_with_llm'} or type(data['share_with_llm']) is not bool:
            return jsonify(error='invalid_request'), 400
        if not data['share_with_llm']:
            return jsonify(error='llm_consent_required'), 400
        problem = validate_inputs(data['features'], data['measurement'])
        if problem:
            return jsonify(error=problem), 400
        try:
            result = run_supervisor({'intent': 'explanation', 'question': 'Giải thích ý nghĩa và giới hạn của các kết quả đánh giá nguy cơ tiểu đường dựa trên tài liệu.',
                                     'features': data['features'], 'measurement': data['measurement'], 'generate_answer': True})
            response = answer_payload(result)
            response['summary'] = summary_for_history(result)
            return jsonify(result=response)
        except Exception:
            return jsonify(error='explanation_unavailable'), 503

    @app.get('/api/history')
    def history():
        owner = token_hash(request.headers['X-Session-Token'])
        try:
            with database(Path(app.config['DATABASE'])) as db:
                rows = db.execute('SELECT id, created_at, summary FROM assessments WHERE owner = ? ORDER BY created_at DESC LIMIT 100', (owner,)).fetchall()
            return jsonify(history=[{'id': row[0], 'created_at': row[1], 'summary': json.loads(row[2])} for row in rows])
        except (sqlite3.Error, OSError, ValueError):
            return jsonify(error='history_unavailable'), 503

    @app.delete('/api/history')
    def delete_history():
        owner = token_hash(request.headers['X-Session-Token'])
        try:
            with database(Path(app.config['DATABASE'])) as db:
                deleted = db.execute('DELETE FROM assessments WHERE owner = ?', (owner,)).rowcount
            return jsonify(deleted=deleted)
        except (sqlite3.Error, OSError):
            return jsonify(error='history_unavailable'), 503

    @app.get('/')
    def index():
        if not (DIST / 'index.html').is_file():
            return 'Frontend chưa được build.', 503
        return send_from_directory(DIST, 'index.html')

    @app.get('/assets/<path:filename>')
    def assets(filename):
        return send_from_directory(DIST / 'assets', filename)

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error='request_too_large'), 413

    return app
