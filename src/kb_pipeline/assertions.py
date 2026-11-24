from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .common import ROOT, read_jsonl, stable_id, write_jsonl


def propose() -> list[dict[str, Any]]:
    """Create review tasks only; a term mention is not a medical assertion."""
    chunks = {item["id"]: item for item in read_jsonl("data/kb/chunks.jsonl")}
    mentions = read_jsonl("data/kg/mentions.jsonl")
    candidates: list[dict[str, Any]] = []
    for mention in mentions:
        chunk = chunks[mention["chunk_id"]]
        candidate = {
            "id": stable_id("assertion_candidate", mention["entity_id"], mention["chunk_id"], mention["start"], mention["end"]),
            "text": mention["matched_text"], "disease_id": mention["entity_id"] if mention["entity_id"].startswith("disease_") else None,
            "concept_ids": [] if mention["entity_id"].startswith("disease_") else [mention["entity_id"]],
            "evidence_chunk_ids": [mention["chunk_id"]], "evidence_quote": chunk["text"], "review_status": "pending",
            "reason": "Dictionary match only; requires expert review before semantic graph export.", "demo": False,
        }
        candidates.append(candidate)
    write_jsonl("data/kg/assertions_candidates.jsonl", candidates)
    return candidates


def apply_review(review_path: str) -> list[dict[str, Any]]:
    candidates = {item["id"]: item for item in read_jsonl("data/kg/assertions_candidates.jsonl")}
    decisions: dict[str, dict[str, str]] = {}
    path = Path(review_path)
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            decisions = {row["assertion_id"]: row for row in csv.DictReader(handle) if row.get("assertion_id")}
    approved: list[dict[str, Any]] = []
    for candidate_id, candidate in candidates.items():
        review = decisions.get(candidate_id)
        if not review or review.get("decision") != "accepted_for_demo":
            continue
        assertion = {**candidate, "review_status": "accepted_for_demo", "reviewer": review.get("reviewer"), "reviewed_at": review.get("reviewed_at"), "review_reason": review.get("reason")}
        approved.append(assertion)
    write_jsonl("data/kg/assertions_approved.jsonl", approved)
    return approved
