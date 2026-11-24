from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pymupdf
from bs4 import BeautifulSoup, Tag

from .common import ROOT, normalise_text, read_jsonl, stable_id, write_jsonl

BLOCKS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"}
NOISE = "script, style, noscript, nav, footer, form, iframe, [role='navigation'], .advertisement, .ads, .comments, .related-posts"


def _text(element: Tag) -> str:
    return normalise_text(element.get_text(" ", strip=True))


def _html_blocks(raw_path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    text = raw_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(text, "lxml")
    for element in soup.select(NOISE):
        element.decompose()
    content = soup.find("article") or soup.find("main") or soup.body or soup
    blocks: list[dict[str, Any]] = []
    section: list[str] = []
    for element in content.find_all(list(BLOCKS)):
        if element.find_parent(["nav", "footer", "aside"]):
            continue
        content_text = _text(element)
        if not content_text:
            continue
        if element.name and re.fullmatch(r"h[1-6]", element.name):
            level = int(element.name[1])
            section = section[: level - 1] + [content_text]
            kind = "heading"
        elif element.name == "table":
            kind = "table"
        else:
            kind = "list_item" if element.name == "li" else "paragraph"
        blocks.append({"kind": kind, "text": content_text, "section_path": section.copy()})
    return "\n\n".join(block["text"] for block in blocks), blocks, {"extraction_method": "beautifulsoup_article_main_body"}


def _pdf_blocks(raw_path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    document = pymupdf.open(raw_path)
    blocks: list[dict[str, Any]] = []
    page_warnings: list[int] = []
    for page_number, page in enumerate(document, start=1):
        page_text = normalise_text(page.get_text("text"))
        if len(page_text) < 40:
            page_warnings.append(page_number)
        if page_text:
            blocks.append({"kind": "page", "text": page_text, "section_path": [f"Trang {page_number}"], "page": page_number})
    return "\n\n".join(block["text"] for block in blocks), blocks, {"extraction_method": "pymupdf_text", "low_text_pages": page_warnings}


def run() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for inventory in read_jsonl("data/interim/html_inventory.jsonl"):
        raw_path = ROOT / inventory["relative_path"]
        try:
            clean_text, blocks, details = _pdf_blocks(raw_path) if inventory["format"] == "pdf" else _html_blocks(raw_path)
            for index, block in enumerate(blocks, start=1):
                block["id"] = stable_id("block", inventory["id"], index, block["text"])
            quality_flags = []
            if len(clean_text) < 300:
                quality_flags.append("too_little_extracted_text")
            if details.get("low_text_pages"):
                quality_flags.append("possible_scanned_pages")
            records.append({"source_id": inventory["id"], "source_path": inventory["relative_path"], "clean_text": clean_text, "blocks": blocks, "quality_flags": quality_flags, "quality_status": "pending" if quality_flags else "accepted", **details})
        except Exception as error:  # continue so one bad source does not discard the rest
            records.append({"source_id": inventory["id"], "source_path": inventory["relative_path"], "clean_text": "", "blocks": [], "quality_flags": ["extraction_error"], "quality_status": "rejected", "error": f"{type(error).__name__}: {error}"})
    write_jsonl("data/interim/documents.jsonl", records)
    write_jsonl("data/interim/extraction_errors.jsonl", [record for record in records if record.get("error") or record["quality_flags"]])
    return records
