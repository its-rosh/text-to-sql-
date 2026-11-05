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

import os
from pathlib import Path
import sys
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_DIR = Path(os.getenv("CHROMA_DB_DIR", ".chroma"))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "conversational_analytics_knowledge")
TOP_K = 3

# Chroma distance: lower is better.
MAX_ALLOWED_DISTANCE = 1.20


def get_or_init_collection(client: chromadb.PersistentClient):
    # Try configured collection first, then fallback to 'rag_metadata'
    for name in [COLLECTION_NAME, "rag_metadata"]:
        try:
            return client.get_collection(name=name)
        except Exception:
            continue

    # Auto-initialize if missing
    metadata_path = Path("reports") / "rag_metadata.txt"
    if metadata_path.exists():
        metadata_text = metadata_path.read_text(encoding="utf-8")
        chunks = [
            chunk.strip()
            for chunk in metadata_text.split("\n\n---\n\n")
            if chunk.strip()
        ]
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        ids = [f"chunk_{index}" for index in range(len(chunks))]
        collection.upsert(ids=ids, documents=chunks)
        return collection

    raise RuntimeError("ChromaDB collection not found and reports/rag_metadata.txt is missing.")


_CACHED_CLIENT = None
_CACHED_COLLECTION = None


def get_cached_collection():
    global _CACHED_CLIENT, _CACHED_COLLECTION
    if _CACHED_COLLECTION is None:
        _CACHED_CLIENT = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        _CACHED_COLLECTION = get_or_init_collection(_CACHED_CLIENT)
    return _CACHED_COLLECTION


def retrieve_context(question: str) -> dict:
    collection = get_cached_collection()

    results = collection.query(
        query_texts=[question],
        n_results=TOP_K,
    )

    return results


def decide_if_evidence_is_enough(results: dict) -> tuple[bool, str]:
    document_groups = results.get("documents")
    distance_groups = results.get("distances")

    if not document_groups or not distance_groups:
        return False, "No RAG evidence was returned."

    documents = document_groups[0]
    distances = distance_groups[0]

    if not documents or not distances:
        return False, "No matching RAG evidence was found."

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
