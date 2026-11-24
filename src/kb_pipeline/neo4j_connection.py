from __future__ import annotations

import os
from pathlib import Path

from neo4j import GraphDatabase

from .common import ROOT

REQUIRED_ENVIRONMENT = ("NEO4J_URI", "NEO4J_DATABASE", "NEO4J_USERNAME", "NEO4J_PASSWORD")


def load_local_environment(path: Path = ROOT / ".env") -> dict[str, str]:
    """Load simple KEY=VALUE lines without logging the password."""
    if not path.exists():
        raise FileNotFoundError(f"Missing local configuration: {path.name}. Copy .env.example to .env.")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    missing = [key for key in REQUIRED_ENVIRONMENT if not values.get(key)]
    if missing:
        raise ValueError(f"Missing Neo4j configuration: {', '.join(missing)}")
    return values


def verify_connection() -> dict[str, object]:
    settings = load_local_environment()
    with GraphDatabase.driver(settings["NEO4J_URI"], auth=(settings["NEO4J_USERNAME"], settings["NEO4J_PASSWORD"])) as driver:
        driver.verify_connectivity()
        with driver.session(database=settings["NEO4J_DATABASE"]) as session:
            record = session.run(
                "MATCH (n) WITH count(n) AS node_count "
                "MATCH ()-[r]->() RETURN node_count, count(r) AS relationship_count"
            ).single()
    return {"uri": settings["NEO4J_URI"], "database": settings["NEO4J_DATABASE"], "node_count": record["node_count"], "relationship_count": record["relationship_count"]}
