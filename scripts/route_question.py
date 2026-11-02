"""
Step 9: Route User Question
Purpose: Decide which table/domain a user question belongs to with dynamic keyword & root stem matching.
Input: User question from terminal or API.
Output: p2c, mab_meb, both_tables, or out_of_scope.
Run: python scripts/route_question.py "Show total MAB by income segment"
"""

import sys
import re

P2C_KEYWORDS = [
    "ucic",
    "customer id",
    "party id",
    "account nbr",
    "account number",
    "source account",
    "account open",
    "account close",
    "open account",
    "closed account",
    "open date",
    "close date",
    "closure",
    "opened in",
    "opened",
    "closed",
    "opening date",
    "closing date",
    "how long",
    "account age",
    "product type",
    "account type",
    "product",
    "savings account",
    "current account",
    "fixed deposit account",
    "recurring deposit",
    "overdraft",
    "loan",
    "credit card",
    "dormancy",
    "dormant",
    "active account",
    "inactive account",
    "nri",
    "service segment",
    "linkage",
    "linked",
    "customer account",
    "tenure",
    "years",
    "open for",
    "running for",
    "shut down",
    "accounts open",
    "accounts closed",
    "scheme type",
    "card block",
    "criteria",
]

P2C_ROOT_STEMS = [
    r"\bopen\w*",     # open, opened, opening, opens
    r"\bclos\w*",     # close, closed, closing, closure
    r"\btenur\w*",    # tenure
    r"\byear\w*",     # year, years
    r"\bage\w*",      # age, aged
    r"\bdorm\w*",     # dormant, dormancy
    r"\blink\w*",     # link, linked, linkage
]

P2C_SHORT_CODES = [
    "sa", "ca", "fd", "rd", "ln", "cc", "od"
]

MAB_MEB_KEYWORDS = [
    "mab",
    "meb",
    "monthly average balance",
    "monthly end balance",
    "average balance",
    "end balance",
    "balance",
    "balances",
    "final segment",
    "income segment",
    "income tier",
    "salaried",
    "salary segment",
    "household segment",
    "bal bucket",
    "fd bucket",
    "fixed deposit balance",
    "branch code",
    "branch",
    "brcode",
    "ledger",
    "managed profile",
    "gl description",
    "gldesc",
    "gl code",
    "glcode",
    "retail",
    "bulk",
    "orig_fdamt",
    "fd amount",
    "deposit amount",
    "employee code",
    "emp code",
    "emp_code",
]

MAB_MEB_ROOT_STEMS = [
    r"\bbal\w*",      # balance, balances, bal_bucket
    r"\bbranch\w*",   # branch, branches, brcode
    r"\bdeposit\w*",  # deposit, deposits
]

OUT_OF_SCOPE_KEYWORDS = [
    "prime minister",
    "president",
    "weather",
    "movie",
    "cricket",
    "football",
    "stock price",
    "news",
    "politics",
    "horoscope",
    "recipe",
]


def count_matches(
    question: str,
    phrases: list[str],
    short_codes: list[str] | None = None,
    root_stems: list[str] | None = None,
) -> int:
    normalized = " " + question.lower() + " "
    score = 0

    for phrase in phrases:
        if phrase in normalized:
            score += 1

    if short_codes:
        for code in short_codes:
            pattern = rf"(?<![a-zA-Z0-9]){re.escape(code)}(?![a-zA-Z0-9])"
            if re.search(pattern, normalized):
                score += 1

    if root_stems:
        for stem in root_stems:
            if re.search(stem, normalized):
                score += 1

    return score


def route_question(question: str) -> dict:
    p2c_score = count_matches(question, P2C_KEYWORDS, P2C_SHORT_CODES, P2C_ROOT_STEMS)
    mab_meb_score = count_matches(question, MAB_MEB_KEYWORDS, None, MAB_MEB_ROOT_STEMS)
    out_of_scope_score = count_matches(question, OUT_OF_SCOPE_KEYWORDS)

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
            "reason": "Question needs customer-account linkage fields and balance/segment fields.",
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
