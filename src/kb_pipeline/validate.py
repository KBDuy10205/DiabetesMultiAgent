from __future__ import annotations

from collections import Counter
from typing import Any

from .common import read_jsonl, write_json


def run() -> dict[str, Any]:
    sources = read_jsonl("data/kb/sources.jsonl")
    chunks = read_jsonl("data/kb/chunks.jsonl")
    entities = read_jsonl("data/kg/entities.jsonl")
    mentions = read_jsonl("data/kg/mentions.jsonl")
    assertions = read_jsonl("data/kg/assertions_approved.jsonl")
    errors: list[str] = []
    warnings: list[str] = []
    ids_by_type = {"source": [item["id"] for item in sources], "chunk": [item["id"] for item in chunks], "entity": [item["id"] for item in entities], "assertion": [item["id"] for item in assertions]}
    for label, values in ids_by_type.items():
        duplicates = [value for value, count in Counter(values).items() if count > 1]
        if duplicates:
            errors.append(f"duplicate {label} IDs: {', '.join(duplicates[:5])}")
    source_ids, chunk_ids, entity_ids = set(ids_by_type["source"]), set(ids_by_type["chunk"]), set(ids_by_type["entity"])
    for source in sources:
        for field in ("id", "source_path", "raw_sha256"):
            if not source.get(field): errors.append(f"source {source.get('id')} missing {field}")
    for chunk in chunks:
        if chunk.get("source_id") not in source_ids: errors.append(f"chunk {chunk['id']} references missing source")
        if not chunk.get("text") or not isinstance(chunk.get("start"), int) or not isinstance(chunk.get("end"), int): errors.append(f"chunk {chunk['id']} has invalid text or offsets")
        if chunk.get("start", 0) >= chunk.get("end", 0): errors.append(f"chunk {chunk['id']} has inverted offsets")
    for mention in mentions:
        if mention.get("chunk_id") not in chunk_ids or mention.get("entity_id") not in entity_ids: errors.append(f"invalid mention {mention}")
    for assertion in assertions:
        if not assertion.get("disease_id") or assertion["disease_id"] not in entity_ids: errors.append(f"assertion {assertion['id']} has no valid disease")
        if not set(assertion.get("evidence_chunk_ids", [])) <= chunk_ids: errors.append(f"assertion {assertion['id']} has invalid evidence")
    if not assertions:
        warnings.append("No reviewed medical assertions: export contains only sources, chunks, entities and mentions.")
    result = {"valid": not errors, "errors": errors, "warnings": warnings, "counts": {"sources": len(sources), "chunks": len(chunks), "entities": len(entities), "mentions": len(mentions), "approved_assertions": len(assertions)}}
    write_json("reports/validation_report.json", result)
    return result
