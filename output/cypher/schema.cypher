CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (n:Source) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (n:Chunk) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT disease_id_unique IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT assertion_id_unique IF NOT EXISTS FOR (n:Assertion) REQUIRE n.id IS UNIQUE;
CREATE INDEX chunk_source_id IF NOT EXISTS FOR (n:Chunk) ON (n.source_id);
