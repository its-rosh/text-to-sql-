"""
Step 5: Search RAG Metadata

Purpose:
Search the RAG metadata and return the most relevant context chunks
for a user's question.

Why this file exists:
Before using ChromaDB, this script helps us understand the basic idea
of retrieval. It reads reports/rag_metadata.txt, splits it into chunks,
compares the user's question with each chunk, and prints the best matches.

Input:
- User question from the terminal
- reports/rag_metadata.txt

Output:
- Top matching metadata chunks
- Similarity score for each chunk

Example:
python scripts/search_rag_metadata.py "Show total MAB by income segment"
"""

from pathlib import Path
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


METADATA_PATH = Path("reports") / "rag_metadata.txt"
TOP_K = 3


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


def retrieve_context(question: str, chunks: list[str]) -> list[tuple[float, str]]:
    documents = [question] + chunks

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(documents)

    question_vector = vectors[0]
    chunk_vectors = vectors[1:]

    scores = cosine_similarity(question_vector, chunk_vectors).flatten()

    ranked_results = sorted(
        zip(scores, chunks),
        key=lambda item: item[0],
        reverse=True,
    )

    return ranked_results[:TOP_K]


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Show total MAB by income segment"

    chunks = load_chunks()
    results = retrieve_context(question, chunks)

    print(f"Question: {question}")
    print("=" * 80)

    for rank, (score, chunk) in enumerate(results, start=1):
        print(f"\nResult {rank}")
        print(f"Score: {score:.4f}")
        print(chunk)


if __name__ == "__main__":
    main()