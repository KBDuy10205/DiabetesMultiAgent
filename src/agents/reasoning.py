from __future__ import annotations

import json
from .settings import llm_settings


class ReasoningAgent:
    """Input: question and retrieved evidence. Output: cited draft or explicit abstention.

    Sends derived ML/rule outputs and retrieved evidence when explicitly requested.
    Original structured results remain available independently of the LLM draft.
    """

    def __init__(self, endpoint=None, model=None, api_key=None, answer_fn=None):
        settings = llm_settings()
        self.endpoint = endpoint or settings['endpoint']
        self.model = model or settings['model']
        self.api_key = api_key or settings['api_key']
        self.answer_fn = answer_fn

    def run(self, question: str, evidence: list, prediction: dict | None = None, rule: dict | None = None) -> dict:
        from rag.core import ABSTAIN, answer
        if not isinstance(question, str) or not question.strip() or not isinstance(evidence, list):
            raise ValueError('Question and evidence list required')
        if not evidence:
            return {'text': ABSTAIN, 'status': 'insufficient_evidence'}
        if not self.endpoint or not self.model:
            return {'text': ABSTAIN, 'status': 'llm_not_configured'}
        summary = {'prediction': prediction, 'rule': rule}
        synthesis = (question + '\n\nKết quả tính toán có sẵn (chép nguyên văn mọi thông điệp cảnh báo an toàn; '
                     'không coi xác suất mô hình là chẩn đoán):\n' + json.dumps(summary, ensure_ascii=False))
        text = (self.answer_fn or answer)(synthesis, evidence, self.endpoint, self.model, self.api_key)
        return {'text': text, 'status': 'insufficient_evidence' if text == ABSTAIN else 'draft'}
