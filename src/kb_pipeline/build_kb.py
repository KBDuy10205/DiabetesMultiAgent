from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import ROOT, read_jsonl, sha256_text, stable_id, write_jsonl


def _chunks(document: dict[str, Any], target: int, minimum: int) -> list[dict[str, Any]]:
    text = document["clean_text"]
    blocks = document["blocks"]
    pieces: list[tuple[int, int, str, list[str], list[str]]] = []
    offset = 0
    for block in blocks:
        start = text.find(block["text"], offset)
        if start < 0:
            continue
        end = start + len(block["text"])
        pieces.append((start, end, block["text"], block.get("section_path", []), [block["id"]]))
        offset = end
    grouped: list[dict[str, Any]] = []
    current: list[tuple[int, int, str, list[str], list[str]]] = []
    current_size = 0
    for piece in pieces:
        if current and current_size + len(piece[2]) > target and current_size >= minimum:
            grouped.append(_make_chunk(document, current, text))
            current, current_size = [], 0
        current.append(piece)
        current_size += len(piece[2]) + 2
    if current:
        grouped.append(_make_chunk(document, current, text))
    return grouped


def _make_chunk(document: dict[str, Any], pieces: list[tuple[int, int, str, list[str], list[str]]], text: str) -> dict[str, Any]:
    start, end = pieces[0][0], pieces[-1][1]
    chunk_text = text[start:end]
    return {
        "id": stable_id("chunk", document["source_id"], "1.0.0", start, end, sha256_text(chunk_text)),
        "source_id": document["source_id"],
        "text": chunk_text,
        "text_sha256": sha256_text(chunk_text),
        "section_path": pieces[-1][3],
        "start": start,
        "end": end,
        "block_ids": [block_id for piece in pieces for block_id in piece[4]],
        "is_summary": False,
        "derived": False,
        "demo": False,
        "quality_status": document["quality_status"],
    }


def run(target: int = 1200, minimum: int = 400) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory = {item["id"]: item for item in read_jsonl("data/interim/html_inventory.jsonl")}
    sources: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    documents_dir = ROOT / "data/kb/documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    for document in read_jsonl("data/interim/documents.jsonl"):
        inventory_record = inventory[document["source_id"]]
        metadata = inventory_record["metadata"]
        sources.append({
            "id": document["source_id"], "title": metadata.get("title") or metadata.get("h1") or Path(document["source_path"]).stem,
            "url": metadata.get("url"), "source_path": document["source_path"], "raw_sha256": inventory_record["raw_sha256"],
            "published_at": metadata.get("published_at"), "accessed_at": metadata.get("accessed_at"), "format": inventory_record["format"],
            "quality_status": document["quality_status"], "quality_flags": document["quality_flags"], "demo": False,
        })
        if document["clean_text"]:
            output = documents_dir / f"{document['source_id']}.md"
            output.write_text(document["clean_text"] + "\n", encoding="utf-8")
            chunks.extend(_chunks(document, target, minimum))
    write_jsonl("data/kb/sources.jsonl", sorted(sources, key=lambda item: item["id"]))
    write_jsonl("data/kb/chunks.jsonl", sorted(chunks, key=lambda item: item["id"]))
    return sources, chunks
