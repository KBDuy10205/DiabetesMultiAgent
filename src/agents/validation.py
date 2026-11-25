from __future__ import annotations

import re


class ValidationAgent:
    """Input: draft and evidence. Output: structural checks, never clinical verification."""

    def run(self, draft: dict, evidence: list, prediction: dict | None = None, rule: dict | None = None) -> dict:
        from rag.core import ABSTAIN
        text = draft.get('text') if isinstance(draft, dict) else None
        if not isinstance(text, str) or not text.strip() or not isinstance(evidence, list):
            return {'valid': False, 'issues': ['invalid_draft_or_evidence'], 'text': ABSTAIN}
        issues = []
        if any(not isinstance(e, dict) or not e.get('chunk_id') or not e.get('source_id') or not e.get('text') for e in evidence):
            issues.append('incomplete_source')
        citations = [int(n) for n in re.findall(r'\[S(\d+)\]', text)]
        if text != ABSTAIN and (not citations or any(n < 1 or n > len(evidence) for n in citations)):
            issues.append('missing_or_invalid_citation')
        if re.search(r'\b(chắc chắn (?:bị|mắc)|chẩn đoán xác định|không cần (?:đi khám|bác sĩ))\b', text, re.IGNORECASE):
            issues.append('unsafe_definitive_claim')
        alerts = (rule or {}).get('alerts', [])
        if text != ABSTAIN and any(not a.get('message') or a['message'] not in text for a in alerts):
            issues.append('safety_alert_missing_or_modified')
        warnings = []
        rule_ids = {r.get('rule_id') for r in (rule or {}).get('results', [])}
        high = {'a1c_at_least_6_5', 'fpg_at_least_126', 'ogtt_at_least_200'}
        if prediction and prediction.get('label') == 0 and rule_ids & high:
            warnings.append('ml_label_and_lab_threshold_differ_do_not_infer_diagnosis')
        return {'valid': not issues, 'issues': issues, 'warnings': warnings, 'text': text if not issues else ABSTAIN,
                'limitation': 'Chỉ kiểm tra cấu trúc, cảnh báo và một số mẫu rủi ro; không xác minh đầy đủ ngữ nghĩa hay an toàn lâm sàng.'}
