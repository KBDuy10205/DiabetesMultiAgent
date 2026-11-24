from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from .common import ROOT, path_from_root, sha256_bytes, stable_id, write_jsonl


def _decode(raw: bytes) -> tuple[str, str, bool]:
    for encoding in ("utf-8-sig", "utf-8", "windows-1258", "latin-1"):
        try:
            text = raw.decode(encoding)
            return text, encoding, "\ufffd" in text
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace", True


def _html_metadata(raw: bytes) -> dict[str, Any]:
    text, encoding, decode_warning = _decode(raw)
    soup = BeautifulSoup(text, "lxml")
    meta: dict[str, Any] = {"encoding": encoding, "decode_warning": decode_warning}
    meta["title"] = soup.title.get_text(" ", strip=True) if soup.title else None
    h1 = soup.find("h1")
    meta["h1"] = h1.get_text(" ", strip=True) if h1 else None
    canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
    meta["canonical_url"] = canonical.get("href") if canonical else None
    for key, attribute, field in (("og:title", "property", "og_title"), ("article:published_time", "property", "published_at"), ("article:modified_time", "property", "modified_at"), ("author", "name", "author")):
        tag = soup.find("meta", attrs={attribute: key})
        meta[field] = tag.get("content").strip() if tag and tag.get("content") else None
    return meta


def _overrides() -> dict[str, dict[str, str]]:
    csv_path = ROOT / "config/source_overrides.csv"
    if not csv_path.exists():
        return {}
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["relative_path"].replace("\\", "/"): row for row in csv.DictReader(handle) if row.get("relative_path")}


def run(input_directory: str = "data/raw") -> list[dict[str, Any]]:
    raw_root = path_from_root(input_directory)
    overrides = _overrides()
    records: list[dict[str, Any]] = []
    supported = {".html", ".htm", ".pdf"}
    for file_path in sorted((item for item in raw_root.rglob("*") if item.is_file() and item.suffix.lower() in supported), key=lambda item: item.as_posix().casefold()):
        raw = file_path.read_bytes()
        relative_path = file_path.relative_to(ROOT).as_posix()
        extension = file_path.suffix.lower()
        metadata: dict[str, Any] = _html_metadata(raw) if extension in {".html", ".htm"} else {"title": file_path.stem, "encoding": None, "decode_warning": False}
        override = overrides.get(relative_path, {})
        url = override.get("url") or metadata.get("canonical_url")
        document_key = url or relative_path
        record = {
            "id": stable_id("source", document_key, sha256_bytes(raw)),
            "relative_path": relative_path,
            "document_key": document_key,
            "format": extension.removeprefix("."),
            "size_bytes": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "status": "pending_extraction",
            "metadata": {
                **metadata,
                "url": url or None,
                "publisher": override.get("publisher") or None,
                "published_at": override.get("published_at") or metadata.get("published_at"),
                "accessed_at": override.get("accessed_at") or None,
            },
        }
        records.append(record)
    duplicate_hashes = Counter(item["raw_sha256"] for item in records)
    for record in records:
        record["duplicate_raw"] = duplicate_hashes[record["raw_sha256"]] > 1
    write_jsonl("data/interim/html_inventory.jsonl", records)
    return records
