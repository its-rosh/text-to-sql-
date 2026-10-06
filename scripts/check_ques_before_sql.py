"""
Step 10: Check Question Before SQL
Purpose: Check if a question is safe and has enough RAG evidence.
Input: User question from terminal.
Output: ALLOW/BLOCK decision before SQL generation.
Run: python scripts/check_question_before_sql.py "Show total MAB by income segment"
"""

import sys

from check_rag_evidence import decide_if_evidence_is_enough
from check_rag_evidence import retrieve_context
from route_question import route_question


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

    rag_results = retrieve_context(question)
    is_evidence_allowed, evidence_reason = decide_if_evidence_is_enough(rag_results)

    if not is_evidence_allowed:
        return {
            "decision": "BLOCK",
            "final_answer": "Not under my knowledge.",
            "reason": evidence_reason,
            "route": route_result["route"],
            "retrieved_context": rag_results["documents"][0],
        }

    return {
        "decision": "ALLOW",
        "final_answer": None,
        "reason": evidence_reason,
        "route": route_result["route"],
        "retrieved_context": rag_results["documents"][0],
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