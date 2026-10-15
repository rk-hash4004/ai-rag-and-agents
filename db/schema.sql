-- pgvector schema for the RAG flows (embedding model: all-minilm, 384 dimensions)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_chunks (
  id            BIGSERIAL PRIMARY KEY,
  source_file   TEXT NOT NULL,
  domain        TEXT,
  document_type TEXT,
  version       TEXT,
  chunk_index   INT  NOT NULL,
  chunk_text    TEXT NOT NULL,
  embedding     VECTOR(384) NOT NULL
);
