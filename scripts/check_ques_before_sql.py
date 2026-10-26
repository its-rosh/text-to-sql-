"""
Step 10: Check Question Before SQL
Purpose: Check if a question is safe and has enough RAG evidence.
Input: User question from terminal.
Output: ALLOW/BLOCK decision before SQL generation.
Run: python scripts/check_ques_before_sql.py "Show total MAB by income segment"
"""

from pathlib import Path
import sys

from check_rag_evidence import decide_if_evidence_is_enough
from check_rag_evidence import retrieve_context
from route_question import route_question


METADATA_PATH = Path("reports") / "rag_metadata.txt"


def load_metadata_chunks() -> list[str]:
    metadata_text = METADATA_PATH.read_text(encoding="utf-8")

    chunks = [
        chunk.strip()
        for chunk in metadata_text.split("\n\n---\n\n")
        if chunk.strip()
    ]

    return chunks


def find_chunk_containing(required_term: str, metadata_chunks: list[str]) -> str | None:
    for chunk in metadata_chunks:
        if required_term in chunk:
            return chunk

    return None


def add_required_context_for_route(route: str, retrieved_context: list[str]) -> list[str]:
    required_terms_by_route = {
        "both_tables": [
            "Table name: p2c",
            "Table name: mab_meb",
            "Join rules:",
            "Business terms:",
        ],
        "p2c": [
            "Table name: p2c",
            "Business terms:",
        ],
        "mab_meb": [
            "Table name: mab_meb",
            "Business terms:",
        ],
    }

    required_terms = required_terms_by_route.get(route, [])
    metadata_chunks = load_metadata_chunks()
    final_context = list(retrieved_context)

    for required_term in required_terms:
        already_present = any(required_term in context for context in final_context)

        if already_present:
            continue

        missing_chunk = find_chunk_containing(required_term, metadata_chunks)

        if missing_chunk:
            final_context.append(missing_chunk)
        else:
            final_context.append(f"Required context missing: {required_term}")

    return final_context


def build_enhanced_question(question: str, route: str) -> str:
    if route == "both_tables":
        return question + " p2c mab_meb source_account_nbr ACCTNO dormancy_status mab_bal meb_bal join"

    if route == "p2c":
        return question + " p2c ucic source_account_nbr dormancy_status product_type account_open_date account_close_date"

    if route == "mab_meb":
        return question + " mab_meb ACCTNO mab_bal meb_bal final_segment income_segment balance"

    return question


def run_pre_sql_checks(question: str) -> dict:
    route_result = route_question(question)

    if route_result["route"] == "out_of_scope":
        return {
            "decision": "BLOCK",
            "final_answer": "Not under my knowledge.",
            "reason": route_result["reason"],
            "route": route_result["route"],
            "retrieved_context": [],
        }

    enhanced_question = build_enhanced_question(question, route_result["route"])

    rag_results = retrieve_context(enhanced_question)
    is_evidence_allowed, evidence_reason = decide_if_evidence_is_enough(rag_results)

    retrieved_context = add_required_context_for_route(
        route_result["route"],
        rag_results["documents"][0],
    )
    missing_context = any(
        context.startswith("Required context missing:")
        for context in retrieved_context
    )

    if missing_context:
        is_evidence_allowed = False
        evidence_reason = "Required table or business context is missing."

    if not is_evidence_allowed:
        return {
            "decision": "BLOCK",
            "final_answer": "Not under my knowledge.",
            "reason": evidence_reason,
            "route": route_result["route"],
            "retrieved_context": retrieved_context,
        }

    return {
        "decision": "ALLOW",
        "final_answer": None,
        "reason": evidence_reason,
        "route": route_result["route"],
        "retrieved_context": retrieved_context,
    }


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Show total MAB by income segment"

    result = run_pre_sql_checks(question)

    print(f"Question: {question}")
    print(f"Decision: {result['decision']}")
    print(f"Route: {result['route']}")
    print(f"Reason: {result['reason']}")

    if result["final_answer"]:
        print(f"Final answer: {result['final_answer']}")

    if result["retrieved_context"]:
        print("\nRetrieved context:")
        print("=" * 80)

        for index, context in enumerate(result["retrieved_context"], start=1):
            print(f"\nContext {index}")
            print(context)


if __name__ == "__main__":
    main()

