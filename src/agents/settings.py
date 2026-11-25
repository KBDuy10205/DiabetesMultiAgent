"""Read optional LLM settings without exposing secrets in logs or errors."""
from __future__ import annotations

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[2] / '.env'
GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
GEMINI_MODEL = 'gemini-4-hydrogen'
KEYS = {'RAG_LLM_ENDPOINT', 'RAG_LLM_MODEL', 'RAG_LLM_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY'}


def llm_settings(path: Path = ENV_PATH) -> dict:
    values = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            key, separator, value = line.strip().partition('=')
            key, value = key.strip(), value.strip()
            if separator and key in KEYS:
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key] = value
    for key in KEYS:
        if key in os.environ:
            values[key] = os.environ[key]
    key = values.get('RAG_LLM_API_KEY') or values.get('GEMINI_API_KEY') or values.get('GOOGLE_API_KEY')
    return {'endpoint': values.get('RAG_LLM_ENDPOINT') or (GEMINI_ENDPOINT if key else None),
            'model': values.get('RAG_LLM_MODEL') or (GEMINI_MODEL if key else None),
            'api_key': key}
