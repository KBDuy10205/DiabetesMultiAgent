from __future__ import annotations

import json
import logging
import multiprocessing as mp
import sys
from dataclasses import dataclass, field
from typing import Any

from .coordinator import CoordinatorAgent
from .knowledge import KnowledgeAgent
from .prediction import PredictionAgent
from .reasoning import ReasoningAgent
from .retrieval import RetrievalAgent
from .rule import RuleAgent
from .validation import ValidationAgent

LOG = logging.getLogger('diabetes.supervisor')
if not LOG.handlers:
    LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)
LOG.propagate = False
ABSTAIN = 'Không đủ bằng chứng trong tài liệu hiện có để trả lời câu hỏi này.'


@dataclass
class SharedState:
    """Per-request ephemeral memory; never passed to the logger as a whole."""
    intent: str
    request: dict = field(repr=False)
    plan: list[str] = field(default_factory=list)
    results: dict[str, dict] = field(default_factory=dict, repr=False)
    evidence: list[dict] = field(default_factory=list, repr=False)
    answer: dict | None = field(default=None, repr=False)
    safety: str = 'not_checked'
    calls: int = 0


def _worker(connection, agent, args):
    try:
        connection.send(('ok', agent.run(*args)))
    except BaseException:
        # Never send exception messages, which can contain input or credentials.
        connection.send(('error', None))
    finally:
        connection.close()


class Supervisor:
    """Coordinator-controlled, sequential execution with killable process timeouts."""

    def __init__(self, coordinator=None, agents=None, timeout_seconds=90, max_calls=7, logger=None):
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or not 0 < timeout_seconds <= 300:
            raise ValueError('timeout_seconds must be > 0 and <= 300')
        if type(max_calls) is not int or not 1 <= max_calls <= 7:
            raise ValueError('max_calls must be 1..7')
        self.coordinator = coordinator or CoordinatorAgent()
        self.agents = agents if agents is not None else {'rule': RuleAgent(), 'prediction': PredictionAgent(), 'retrieval': RetrievalAgent(), 'knowledge': KnowledgeAgent(), 'reasoning': ReasoningAgent(), 'validation': ValidationAgent()}
        self.timeout = timeout_seconds
        self.max_calls = max_calls
        self.logger = logger or LOG
        self.context = mp.get_context('spawn')

    def _log(self, name, status):
        # Only allowlisted constant values; never log requests, results or exceptions.
        assert name in {'supervisor', 'rule', 'prediction', 'retrieval', 'knowledge', 'reasoning', 'validation'}
        assert status in {'start', 'ok', 'error', 'timeout', 'limit', 'blocked', 'complete'}
        self.logger.info('agent=%s status=%s', name, status)

    def _call(self, state, name, *args):
        if state.calls >= self.max_calls:
            self._log(name, 'limit')
            return {'status': 'limit'}
        state.calls += 1
        self._log(name, 'start')
        parent, child = self.context.Pipe(duplex=False)
        process = self.context.Process(target=_worker, args=(child, self.agents[name], args))
        try:
            process.start()
            child.close()
            if not parent.poll(self.timeout):
                status, data = 'timeout', None
            else:
                try:
                    status, data = parent.recv()
                except (EOFError, OSError):
                    status, data = 'error', None
        except Exception:
            status, data = 'error', None
        finally:
            child.close()
            parent.close()
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=2)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=2)
                process.close()
        self._log(name, status)
        return {'status': status, **({'data': data} if status == 'ok' else {})}

    def run(self, request: dict) -> dict:
        if not isinstance(request, dict):
            raise ValueError('Request must be an object')
        allowed = {'intent', 'question', 'features', 'measurement', 'generate_answer'}
        if set(request) - allowed:
            raise ValueError('Unknown request field')
        intent = request.get('intent')
        if intent is None:
            intent = 'explanation' if 'question' in request and ('features' in request or 'measurement' in request) else 'risk' if ('features' in request or 'measurement' in request) else 'knowledge' if 'question' in request else None
        if intent not in {'risk', 'knowledge', 'explanation'}:
            raise ValueError('intent must be risk, knowledge or explanation')
        generate = request.get('generate_answer', False)
        if type(generate) is not bool or (generate and intent == 'risk'):
            raise ValueError('generate_answer requires knowledge or explanation intent')
        if intent in {'knowledge', 'explanation'} and (not isinstance(request.get('question'), str) or not request['question'].strip()):
            raise ValueError('A non-empty question is required')
        if intent == 'risk' and 'features' not in request and 'measurement' not in request:
            raise ValueError('risk requires features or measurement')
        if intent == 'risk' and 'question' in request:
            raise ValueError('risk does not accept question; use explanation')
        if intent == 'knowledge' and ('features' in request or 'measurement' in request):
            raise ValueError('knowledge does not accept health inputs; use explanation')
        if intent == 'explanation' and 'features' not in request and 'measurement' not in request:
            raise ValueError('explanation requires features or measurement')
        # Reuse the coordinator's existing input validation and task selection.
        select = {k: v for k, v in request.items() if k in {'question', 'features', 'measurement'}}
        if intent == 'risk':
            select.pop('question', None)
        if intent == 'knowledge':
            select = {'question': request['question']}
        plan = self.coordinator.run(select)
        state = SharedState(intent=intent, request=request, plan=plan['tasks'])
        self._log('supervisor', 'start')
        if 'measurement' in select:
            state.results['rule'] = self._call(state, 'rule', request['measurement'])
            rule = state.results['rule'].get('data') or {}
            valid_structure = isinstance(rule, dict) and all(isinstance(rule.get(k), list) for k in ('issues', 'alerts', 'results'))
            issues = rule['issues'] if valid_structure else []
            invalid = not valid_structure or any(not isinstance(issue, dict) or issue.get('code') != 'interpretation_not_supported' for issue in issues)
            measurement = request['measurement']
            is_glucose = isinstance(measurement, dict) and measurement.get('test_type') in {'fpg', 'ogtt_2h', 'glucose_random', 'glucose_meter'}
            if state.results['rule']['status'] != 'ok' or (valid_structure and rule['alerts']) or invalid:
                state.safety = 'blocked'
            elif not is_glucose:
                state.safety = 'blocked_missing_glucose'
            else:
                state.safety = 'passed_limited'
        elif 'features' in select:
            state.safety = 'blocked_missing_measurement'
        else:
            state.safety = 'not_applicable'
        if 'prediction' in state.plan:
            if state.safety == 'passed_limited':
                state.results['prediction'] = self._call(state, 'prediction', request['features'])
            else:
                self._log('prediction', 'blocked')
                state.results['prediction'] = {'status': 'blocked_by_safety'}
        for name in ('retrieval', 'knowledge'):
            if name in state.plan:
                state.results[name] = self._call(state, name, request['question'])
        from rag.core import fuse
        vector = state.results.get('retrieval', {}).get('data', {}).get('results', [])
        graph = state.results.get('knowledge', {}).get('data', {}).get('mentions', [])
        if vector or graph:
            try:
                state.evidence = fuse(vector, graph, 5)
            except (KeyError, TypeError, ValueError):
                state.evidence = []
        if generate:
            prediction = state.results.get('prediction', {}).get('data')
            rule = state.results.get('rule', {}).get('data')
            draft = self._call(state, 'reasoning', request['question'], state.evidence, prediction, rule)
            state.results['reasoning'] = {'status': draft['status']}
            if draft['status'] == 'ok':
                checked = self._call(state, 'validation', draft['data'], state.evidence, prediction, rule)
                state.results['validation'] = {'status': checked['status']}
                state.answer = {'draft_status': draft['data'].get('status'), **checked['data']} if checked['status'] == 'ok' else {'valid': False, 'text': ABSTAIN, 'issues': ['validation_unavailable']}
            else:
                state.answer = {'valid': False, 'text': ABSTAIN, 'issues': ['reasoning_unavailable']}
        self._log('supervisor', 'complete')
        return {'intent': state.intent, 'plan': state.plan, 'safety': state.safety, 'calls': state.calls,
                'agents': state.results, 'evidence': state.evidence, 'answer': state.answer,
                'disclaimer': 'Chỉ phục vụ học tập và tham khảo; không thay thế bác sĩ.'}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        request = json.load(sys.stdin)
        result = CoordinatorAgent().supervise(request)
    except (ValueError, TypeError, json.JSONDecodeError):
        print(json.dumps({'error': 'invalid_request'}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if any(v['status'] != 'ok' for v in result['agents'].values()) else 0


if __name__ == '__main__':
    mp.freeze_support()
    raise SystemExit(main())
