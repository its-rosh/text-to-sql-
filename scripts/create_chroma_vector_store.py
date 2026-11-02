"""
Step 6: Create Chroma Vector Store
Purpose: Store RAG metadata chunks inside ChromaDB so they can be searched later.
Input: reports/rag_metadata.txt and settings from .env.
Output: Local ChromaDB database inside .chroma/
"""

import os
from pathlib import Path
import chromadb
from dotenv import load_dotenv

load_dotenv()

METADATA_PATH = Path("reports") / "rag_metadata.txt"
CHROMA_DB_DIR = Path(os.getenv("CHROMA_DB_DIR", ".chroma"))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "rag_metadata")


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

    # Support both primary collection and legacy 'rag_metadata' collection
    collection_names = list({COLLECTION_NAME, "rag_metadata"})

    for col_name in collection_names:
        collection = client.get_or_create_collection(name=col_name)
        ids = [f"chunk_{index}" for index in range(len(chunks))]
        collection.upsert(
            ids=ids,
            documents=chunks,
        )

    print(f"Stored {len(chunks)} chunks in ChromaDB collections: {collection_names}.")
    print(f"ChromaDB directory: {CHROMA_DB_DIR}")


def main() -> None:
    chunks = load_chunks()
    create_vector_store(chunks)


if __name__ == "__main__":
    main()
