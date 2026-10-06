"""
Step 9: Route User Question
Purpose: Decide which table/domain a user question belongs to.
Input: User question from terminal.
Output: p2c, mab_meb, both_tables, or out_of_scope.
Run: python scripts/route_question.py "Show total MAB by income segment"
"""

import sys


P2C_KEYWORDS = [
    "ucic",
    "account open",
    "account close",
    "open account",
    "closed account",
    "product type",
    "dormancy",
    "dormant",
    "nri",
    "service segment",
    "linkage",
    "linked",
    "customer account",
]

MAB_MEB_KEYWORDS = [
    "mab",
    "meb",
    "monthly average balance",
    "monthly end balance",
    "balance",
    "final segment",
    "income segment",
    "bal bucket",
    "fd bucket",
    "fixed deposit",
]

OUT_OF_SCOPE_KEYWORDS = [
    "prime minister",
    "weather",
    "movie",
    "cricket",
    "stock price",
    "news",
]

#counting how many words appear in the question 
def count_keyword_matches(question: str, keywords: list[str]) -> int:
    normalized_question = question.lower()

    match_count = 0

    for keyword in keywords:
        if keyword in normalized_question:
            match_count += 1

    return match_count


def route_question(question: str) -> dict:
    p2c_score = count_keyword_matches(question, P2C_KEYWORDS)
    mab_meb_score = count_keyword_matches(question, MAB_MEB_KEYWORDS)
    out_of_scope_score = count_keyword_matches(question, OUT_OF_SCOPE_KEYWORDS)

    if out_of_scope_score > 0:
        return {
            "route": "out_of_scope",
            "reason": "Question contains out-of-scope keywords.",
            "p2c_score": p2c_score,
            "mab_meb_score": mab_meb_score,
        }

    if p2c_score > 0 and mab_meb_score > 0:
        return {
            "route": "both_tables",
            "reason": "Question needs account/customer fields and balance fields.",
            "p2c_score": p2c_score,
            "mab_meb_score": mab_meb_score,
        }

    if p2c_score > 0:
        return {
            "route": "p2c",
            "reason": "Question matches customer-account linkage fields.",
            "p2c_score": p2c_score,
            "mab_meb_score": mab_meb_score,
        }

    if mab_meb_score > 0:
        return {
            "route": "mab_meb",
            "reason": "Question matches balance or segment fields.",
            "p2c_score": p2c_score,
            "mab_meb_score": mab_meb_score,
        }

    return {
        "route": "out_of_scope",
        "reason": "Question does not clearly match known project data.",
        "p2c_score": p2c_score,
        "mab_meb_score": mab_meb_score,
    }


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "Show total MAB by income segment"

    result = route_question(question)

    print(f"Question: {question}")
    print(f"Route: {result['route']}")
    print(f"Reason: {result['reason']}")
    print(f"P2C score: {result['p2c_score']}")
    print(f"MAB/MEB score: {result['mab_meb_score']}")


if __name__ == "__main__":
    main()