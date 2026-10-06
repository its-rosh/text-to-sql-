"""
Step 12: Check SQL Reliability
Purpose: Check if SQL matches the user's analytics question.
Input: User question and SQL text.
Output: PASS or REVIEW with reason.
Run: python scripts/check_sql_reliability.py "Show total MAB by income segment" "SELECT income_segment, SUM(mab_bal) FROM mab_meb GROUP BY income_segment"
"""

import sys


QUESTION_TO_SQL_RULES = [
    {
        "question_terms": ["total", "mab"],
        "required_sql_terms": ["sum", "mab_bal"],
        "reason": "Question asks for total MAB, so SQL should use SUM(mab_bal).",
    },
    {
        "question_terms": ["average", "mab"],
        "required_sql_terms": ["avg", "mab_bal"],
        "reason": "Question asks for average MAB, so SQL should use AVG(mab_bal).",
    },
    {
        "question_terms": ["total", "meb"],
        "required_sql_terms": ["sum", "meb_bal"],
        "reason": "Question asks for total MEB, so SQL should use SUM(meb_bal).",
    },
    {
        "question_terms": ["average", "meb"],
        "required_sql_terms": ["avg", "meb_bal"],
        "reason": "Question asks for average MEB, so SQL should use AVG(meb_bal).",
    },
    {
        "question_terms": ["income segment"],
        "required_sql_terms": ["income_segment"],
        "reason": "Question asks by income segment, so SQL should use income_segment.",
    },
    {
        "question_terms": ["final segment"],
        "required_sql_terms": ["final_segment"],
        "reason": "Question asks by final segment, so SQL should use final_segment.",
    },
    {
        "question_terms": ["product type"],
        "required_sql_terms": ["product_type"],
        "reason": "Question asks by product type, so SQL should use product_type.",
    },
    {
        "question_terms": ["dormant", "dormancy"],
        "required_sql_terms": ["dormancy_status"],
        "reason": "Question asks about dormancy, so SQL should use dormancy_status.",
    },
]


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def all_terms_present(text: str, terms: list[str]) -> bool:
    for term in terms:
        if term not in text:
            return False

    return True


def check_sql_reliability(question: str, sql: str) -> dict:
    normalized_question = normalize_text(question)
    normalized_sql = normalize_text(sql)

    review_reasons = []

    for rule in QUESTION_TO_SQL_RULES:
        question_matches_rule = all_terms_present(
            normalized_question,
            rule["question_terms"],
        )

        if question_matches_rule:
            sql_has_required_terms = all_terms_present(
                normalized_sql,
                rule["required_sql_terms"],
            )

            if not sql_has_required_terms:
                review_reasons.append(rule["reason"])

    if review_reasons:
        return {
            "decision": "REVIEW",
            "reason": " ".join(review_reasons),
        }

    return {
        "decision": "PASS",
        "reason": "SQL matches the basic question requirements.",
    }


def main() -> None:
    if len(sys.argv) >= 3:
        question = sys.argv[1]
        sql = sys.argv[2]
    else:
        question = "Show total MAB by income segment"
        sql = "SELECT income_segment, SUM(mab_bal) FROM mab_meb GROUP BY income_segment"

    result = check_sql_reliability(question, sql)

    print(f"Question: {question}")
    print(f"SQL: {sql}")
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    main()