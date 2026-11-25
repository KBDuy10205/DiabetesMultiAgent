from __future__ import annotations


class KnowledgeAgent:
    """Input: question and limit. Output: matched entities, mentions and reviewed assertions."""

    def __init__(self, connection_factory=None, entity_loader=None, mention_search=None, assertion_search=None):
        self.connection_factory, self.entity_loader = connection_factory, entity_loader
        self.mention_search, self.assertion_search = mention_search, assertion_search

    def run(self, question: str, limit: int = 20) -> dict:
        if not isinstance(question, str) or not question.strip() or type(limit) is not int or not 1 <= limit <= 40:
            raise ValueError('A non-empty question and limit between 1 and 40 are required')
        from kb_pipeline.common import read_jsonl
        from rag.core import connect, graph_assertions, graph_search, match_entities
        entities = (self.entity_loader or (lambda: read_jsonl('data/kg/entities.jsonl')))()
        ids = match_entities(question, entities)
        if not ids:
            return {'entity_ids': [], 'mentions': [], 'assertions': []}
        driver, database = (self.connection_factory or connect)()
        try:
            return {'entity_ids': ids,
                    'mentions': (self.mention_search or graph_search)(driver, database, ids, limit),
                    'assertions': (self.assertion_search or graph_assertions)(driver, database, ids, limit)}
        finally:
            driver.close()
