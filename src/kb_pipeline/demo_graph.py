"""Small explicitly unreviewed graph for educational use, separate from Assertion."""
from __future__ import annotations

import argparse
import json
import sys

from .common import read_jsonl
from .neo4j_connection import load_local_environment
from neo4j import GraphDatabase

DATA = 'data/kg/demo_relations.jsonl'


def validate(records, chunks, entities):
    chunk_by_id = {c['id']: c for c in chunks}
    diseases = {e['id'] for e in entities if e['label'] == 'Disease'}
    ids = set()
    for row in records:
        if row['id'] in ids:
            raise ValueError('Duplicate demo relation ID')
        ids.add(row['id'])
        chunk = chunk_by_id.get(row['chunk_id'])
        if (row.get('demo') is not True or row.get('review_status') != 'demo_unreviewed'
                or row.get('relation') != 'HAS_POSSIBLE_SYMPTOM'
                or not row.get('concept_id') or not row.get('concept_name')
                or row.get('disease_id') not in diseases or not chunk
                or chunk.get('source_id') != row.get('source_id')
                or not row.get('evidence_quote') or row['evidence_quote'] not in chunk['text']
                or row['concept_name'].casefold() not in row['evidence_quote'].casefold()):
            raise ValueError(f"Invalid evidence or demo metadata for {row['id']}")
    if not records:
        raise ValueError('Demo dataset is empty')


def import_demo(driver, database, records):
    def write(tx):
        for row in records:
            record = tx.run('''MATCH (d:Disease {id:$disease_id}), (c:Chunk {id:$chunk_id})-[:FROM_SOURCE]->(s:Source {id:$source_id})
                WHERE c.text CONTAINS $evidence_quote
                MERGE (x:DemoConcept {id:$concept_id}) SET x.name=$concept_name, x.demo=true, x.review_status='demo_unreviewed'
                MERGE (a:DemoAssertion {id:$id}) SET a.relation=$relation, a.evidence_quote=$evidence_quote, a.demo=true, a.review_status='demo_unreviewed'
                MERGE (d)-[:HAS_DEMO_ASSERTION]->(a)
                MERGE (a)-[:DEMO_ABOUT]->(x)
                MERGE (a)-[:DEMO_SUPPORTED_BY]->(c)
                RETURN count(a) AS count''', **row).single()
            if record['count'] != 1:
                raise ValueError(f"Graph evidence missing or inconsistent for {row['id']}")
    with driver.session(database=database) as session:
        session.execute_write(write)


def query_demo(driver, database):
    with driver.session(database=database) as session:
        return [dict(row) for row in session.run('''MATCH (d:Disease)-[:HAS_DEMO_ASSERTION]->(a:DemoAssertion)-[:DEMO_ABOUT]->(x:DemoConcept),
            (a)-[:DEMO_SUPPORTED_BY]->(c:Chunk)-[:FROM_SOURCE]->(s:Source)
            RETURN d.name AS disease, a.id AS id, a.relation AS relation, x.name AS concept,
                   a.review_status AS review_status, a.demo AS demo, a.evidence_quote AS evidence_quote,
                   c.id AS chunk_id, s.id AS source_id, s.title AS source_title, s.url AS url
            ORDER BY id''')]


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Load or inspect the educational demo graph')
    parser.add_argument('command', choices=['import', 'query'])
    args = parser.parse_args()
    records = read_jsonl(DATA)
    validate(records, read_jsonl('data/kb/chunks.jsonl'), read_jsonl('data/kg/entities.jsonl'))
    settings = load_local_environment()
    with GraphDatabase.driver(settings['NEO4J_URI'], auth=(settings['NEO4J_USERNAME'], settings['NEO4J_PASSWORD'])) as driver:
        if args.command == 'import':
            import_demo(driver, settings['NEO4J_DATABASE'], records)
        print(json.dumps(query_demo(driver, settings['NEO4J_DATABASE']), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
