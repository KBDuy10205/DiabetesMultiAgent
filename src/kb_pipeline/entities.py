from __future__ import annotations

import re
import unicodedata
from typing import Any

from .common import read_json, read_jsonl, write_jsonl


def _normalise(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def run() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entities: list[dict[str, Any]] = read_json("config/entity_dictionary.json", [])
    mentions: list[dict[str, Any]] = []
    for chunk in read_jsonl("data/kb/chunks.jsonl"):
        haystack = _normalise(chunk["text"])
        for entity in entities:
            for alias in entity.get("aliases", []):
                pattern = re.compile(r"(?<!\w)" + re.escape(_normalise(alias)) + r"(?!\w)")
                for match in pattern.finditer(haystack):
                    mentions.append({"chunk_id": chunk["id"], "entity_id": entity["id"], "matched_text": chunk["text"][match.start():match.end()], "start": match.start(), "end": match.end()})
    # Same entity may match through two aliases at identical offsets.
    mentions = list({(item["chunk_id"], item["entity_id"], item["start"], item["end"]): item for item in mentions}.values())
    write_jsonl("data/kg/entities.jsonl", sorted(entities, key=lambda item: item["id"]))
    write_jsonl("data/kg/mentions.jsonl", sorted(mentions, key=lambda item: (item["chunk_id"], item["start"], item["entity_id"])))
    return entities, mentions
