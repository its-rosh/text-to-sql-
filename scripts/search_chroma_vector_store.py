"""
Step 7: Search Chroma Vector Store

Purpose:
Search the local ChromaDB vector store for the best RAG context.
Input: User question and .chroma/ vector database.
Output: Top matching metadata chunks with distance score for each match.
"""

import os
from pathlib import Path
import sys
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_DIR = Path(os.getenv("CHROMA_DB_DIR", ".chroma"))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "conversational_analytics_knowledge")
TOP_K = 3


def search_vector_store(question: str) -> dict:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    collection = None
    for name in [COLLECTION_NAME, "rag_metadata"]:
        try:
            collection = client.get_collection(name=name)
            break
        except Exception:
            continue

    if collection is None:
        raise RuntimeError(f"Collection {COLLECTION_NAME} not found in ChromaDB.")

    results = collection.query(
        query_texts=[question],
        n_results=TOP_K,
    )

    return results


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Show total MAB by income segment"

    results = search_vector_store(question)

    documents = results["documents"][0]
    distances = results["distances"][0]

    print(f"Question: {question}")
    print("=" * 80)

    for rank, (distance, document) in enumerate(zip(distances, documents), start=1):
        print(f"\nResult {rank}")
        print(f"Distance: {distance:.4f}")
        print(document)


if __name__ == "__main__":
    main()
