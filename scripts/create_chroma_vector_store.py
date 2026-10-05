"""
Step 6: Create Chroma Vector Store

Purpose:
Store RAG metadata chunks inside ChromaDB so they can be searched later.

Why this file exists:
Our previous search script used temporary TF-IDF search. That helped us learn
retrieval. This script creates a persistent local vector store using ChromaDB.

Input:
- reports/rag_metadata.txt

Output:
- Local ChromaDB database inside .chroma/
- Collection named rag_metadata

Important:
This script stores metadata text chunks, not raw Excel data rows.
"""

from pathlib import Path

import chromadb


METADATA_PATH = Path("reports") / "rag_metadata.txt"
CHROMA_DB_DIR = Path(".chroma")
COLLECTION_NAME = "rag_metadata"


def load_chunks() -> list[str]:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {METADATA_PATH}")

    metadata_text = METADATA_PATH.read_text(encoding="utf-8")

    chunks = [
        chunk.strip()
        for chunk in metadata_text.split("\n\n---\n\n")
        if chunk.strip()
    ]

    return chunks


def create_vector_store(chunks: list[str]) -> None:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    ids = [f"chunk_{index}" for index in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
    )

    print(f"Stored {len(chunks)} chunks in ChromaDB.")
    print(f"ChromaDB directory: {CHROMA_DB_DIR}")
    print(f"Collection name: {COLLECTION_NAME}")


def main() -> None:
    chunks = load_chunks()
    create_vector_store(chunks)


if __name__ == "__main__":
    main()

