"""
Step 7: Search Chroma Vector Store

Purpose:
Search the local ChromaDB vector store for the best RAG context.

Input:
- User question
- .chroma/ vector database
Output:
- Top matching metadata chunks
- Distance score for each match
"""

from pathlib import Path
import sys

import chromadb


CHROMA_DB_DIR = Path(".chroma")
COLLECTION_NAME = "rag_metadata"
TOP_K = 3


def search_vector_store(question: str) -> dict:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    collection = client.get_collection(name=COLLECTION_NAME)

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