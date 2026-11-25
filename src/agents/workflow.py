from __future__ import annotations

from .coordinator import CoordinatorAgent
from .knowledge import KnowledgeAgent
from .prediction import PredictionAgent
from .reasoning import ReasoningAgent
from .retrieval import RetrievalAgent
from .rule import RuleAgent
from .validation import ValidationAgent


class AgentWorkflow:
    """Route structured requests; preserve per-agent errors and deterministic alerts."""

    def __init__(self, coordinator=None, prediction=None, rule=None, retrieval=None, knowledge=None, reasoning=None, validation=None):
        self.coordinator = coordinator or CoordinatorAgent()
        self.agents = {'prediction': prediction or PredictionAgent(), 'rule': rule or RuleAgent(),
                       'retrieval': retrieval or RetrievalAgent(), 'knowledge': knowledge or KnowledgeAgent()}
        self.reasoning, self.validation = reasoning or ReasoningAgent(), validation or ValidationAgent()

    def run(self, request: dict) -> dict:
        from rag.core import ABSTAIN, fuse
        plan = self.coordinator.run(request)
        output = {'plan': plan, 'agents': {}, 'evidence': [], 'answer': None,
                  'disclaimer': 'Chỉ phục vụ học tập và tham khảo; không thay thế bác sĩ.'}
        # Always preserve and return a completed safety-rule result even if another agent fails.
        order = [t for t in ['rule', 'prediction', 'retrieval', 'knowledge'] if t in plan['tasks']]
        for task in order:
            payload = request[{'rule': 'measurement', 'prediction': 'features', 'retrieval': 'question', 'knowledge': 'question'}[task]]
            try:
                output['agents'][task] = {'status': 'ok', 'data': self.agents[task].run(payload)}
            except Exception as error:
                output['agents'][task] = {'status': 'error', 'error_type': type(error).__name__}
        vector = output['agents'].get('retrieval', {}).get('data', {}).get('results', [])
        graph = output['agents'].get('knowledge', {}).get('data', {}).get('mentions', [])
        if vector or graph:
            output['evidence'] = fuse(vector, graph, limit=5)
        if plan['generate_answer']:
            try:
                prediction = output['agents'].get('prediction', {}).get('data')
                rule = output['agents'].get('rule', {}).get('data')
                draft = self.reasoning.run(request['question'], output['evidence'], prediction, rule)
                output['answer'] = {'draft_status': draft.get('status'), **self.validation.run(draft, output['evidence'], prediction, rule)}
            except Exception as error:
                output['answer'] = {'valid': False, 'text': ABSTAIN, 'issues': ['reasoning_or_validation_failed'], 'error_type': type(error).__name__}
        return output
