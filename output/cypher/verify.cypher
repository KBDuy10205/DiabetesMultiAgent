MATCH (n) RETURN labels(n) AS labels, count(*) AS count ORDER BY labels;
MATCH ()-[r]->() RETURN type(r) AS relationship_type, count(*) AS count ORDER BY relationship_type;
MATCH (ch:Chunk) WHERE NOT EXISTS { MATCH (ch)-[:FROM_SOURCE]->(:Source) } RETURN ch.id AS chunk_without_source;
MATCH (a:Assertion) WHERE NOT EXISTS { MATCH (a)-[r]->(:Chunk)-[:FROM_SOURCE]->(:Source) WHERE type(r) = 'SUPPORTED_BY' } RETURN a.id AS assertion_without_evidence;
