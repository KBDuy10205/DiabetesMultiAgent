from __future__ import annotations


class CoordinatorAgent:
    """Input: structured request. Output: ordered agent selection, without LLM."""

    def run(self, request: dict) -> dict:
        if not isinstance(request, dict):
            raise ValueError('Request must be an object')
        allowed = {'question', 'features', 'measurement', 'tasks', 'generate_answer'}
        if set(request) - allowed:
            raise ValueError(f'Unknown request fields: {sorted(set(request) - allowed)}')
        question = request.get('question')
        if question is not None and (not isinstance(question, str) or not question.strip()):
            raise ValueError('question must be a non-empty string')
        tasks = request.get('tasks')
        if tasks is None:
            tasks = (['prediction'] if 'features' in request else []) + (['rule'] if 'measurement' in request else []) + (['retrieval', 'knowledge'] if question else [])
        elif not isinstance(tasks, list) or not tasks or any(t not in {'prediction', 'rule', 'retrieval', 'knowledge'} for t in tasks) or len(tasks) != len(set(tasks)):
            raise ValueError('tasks must be a non-empty list of unique supported tasks')
        for task, field in [('prediction', 'features'), ('rule', 'measurement'), ('retrieval', 'question'), ('knowledge', 'question')]:
            if task in tasks and field not in request:
                raise ValueError(f'{task} requires {field}')
        if not tasks:
            raise ValueError('No actionable input')
        generate = request.get('generate_answer', False)
        if type(generate) is not bool or (generate and 'retrieval' not in tasks):
            raise ValueError('generate_answer requires retrieval and a boolean value')
        return {'tasks': tasks, 'generate_answer': generate}

    def supervise(self, request: dict, **options) -> dict:
        """Run the bounded supervisor workflow while keeping this coordinator central."""
        from .supervisor import Supervisor
        return Supervisor(coordinator=self, **options).run(request)
