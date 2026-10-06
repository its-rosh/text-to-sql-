"""
Step 8: Check RAG Evidence

Purpose:
Decide whether retrieved RAG context is strong enough to answer a question.

Input:
- User question
- .chroma/ vector database
Output:
- ALLOW if evidence is strong enough
- BLOCK if evidence is weak
- Retrieved context and distance scores
"""

from pathlib import Path
import sys

import chromadb


CHROMA_DB_DIR = Path(".chroma")
COLLECTION_NAME = "rag_metadata"
TOP_K = 3

# Chroma distance: lower is better.
# This starting threshold is simple and may be tuned later.
MAX_ALLOWED_DISTANCE = 1.20


def retrieve_context(question: str) -> dict:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)

    results = collection.query(
        query_texts=[question],
        n_results=TOP_K,
    )

    return results


def decide_if_evidence_is_enough(results: dict) -> tuple[bool, str]:
    distances = results["distances"][0]

    best_distance = min(distances)

    if best_distance <= MAX_ALLOWED_DISTANCE:
        return True, f"Evidence allowed. Best distance: {best_distance:.4f}"

    return False, f"Evidence blocked. Best distance: {best_distance:.4f}"


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Show total MAB by income segment"

    results = retrieve_context(question)
    is_allowed, reason = decide_if_evidence_is_enough(results)

    print(f"Question: {question}")
    print(reason)

    if is_allowed:
        print("\nDecision: ALLOW")
    else:
        print("\nDecision: BLOCK")
        print("Final answer: Not under my knowledge.")

    print("\nRetrieved context:")
    print("=" * 80)

    documents = results["documents"][0]
    distances = results["distances"][0]

    for rank, (distance, document) in enumerate(zip(distances, documents), start=1):
        print(f"\nResult {rank}")
        print(f"Distance: {distance:.4f}")
        print(document)


if __name__ == "__main__":
    main()