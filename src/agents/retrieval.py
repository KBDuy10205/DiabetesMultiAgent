from __future__ import annotations


class RetrievalAgent:
    """Input: question and limit. Output: source-bearing vector search results."""

    def __init__(self, search=None, model_factory=None, connection_factory=None):
        self.search, self.model_factory, self.connection_factory = search, model_factory, connection_factory

    def run(self, question: str, limit: int = 10) -> dict:
        if not isinstance(question, str) or not question.strip() or type(limit) is not int or not 1 <= limit <= 40:
            raise ValueError('A non-empty question and limit between 1 and 40 are required')
        from rag.core import connect, embedder, vector_search
        model = (self.model_factory or embedder)()
        driver, database = (self.connection_factory or connect)()
        try:
            rows = (self.search or vector_search)(driver, database, model, question, limit)
            return {'results': rows}
        finally:
            driver.close()
