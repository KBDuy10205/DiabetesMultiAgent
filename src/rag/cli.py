from __future__ import annotations

import argparse
import json
import os
import sys

from kb_pipeline.common import read_jsonl
from .core import answer, build_index, connect, embedder, fuse, graph_assertions, graph_search, match_entities, vector_search


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Vector and KG retrieval over the existing KB')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('index')
    search = commands.add_parser('search')
    search.add_argument('question')
    search.add_argument('--mode', choices=['vector', 'hybrid'], default='hybrid')
    search.add_argument('--limit', type=int, default=5)
    search.add_argument('--answer', action='store_true')
    args = parser.parse_args()
    if args.command == 'search' and (not args.question.strip() or not 1 <= args.limit <= 20):
        parser.error('Question must not be empty; limit must be between 1 and 20.')
    model = embedder()
    driver, database = connect()
    try:
        if args.command == 'index':
            print(f'Indexed {build_index(driver, database, model)} passages.')
            return
        vector = vector_search(driver, database, model, args.question, limit=40)
        ids = match_entities(args.question, read_jsonl('data/kg/entities.jsonl'))
        graph = graph_search(driver, database, ids, limit=40) if args.mode == 'hybrid' else []
        assertions = graph_assertions(driver, database, ids) if args.mode == 'hybrid' else []
        results = fuse(vector, graph, args.limit)
        print(json.dumps({'matched_entity_ids': ids, 'reviewed_assertions': assertions, 'results': results}, ensure_ascii=False, indent=2))
        if args.answer:
            endpoint = os.environ.get('RAG_LLM_ENDPOINT')
            llm_model = os.environ.get('RAG_LLM_MODEL')
            if not endpoint or not llm_model:
                raise ValueError('Set RAG_LLM_ENDPOINT and RAG_LLM_MODEL for an OpenAI-compatible chat endpoint.')
            print('\n' + answer(args.question, results, endpoint, llm_model, os.environ.get('RAG_LLM_API_KEY')))
    finally:
        driver.close()


if __name__ == '__main__':
    main()
