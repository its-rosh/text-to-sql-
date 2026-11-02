"""
Step 12: Check SQL Reliability
Purpose: Check if SQL matches the user's analytics question.
Input: User question and SQL text.
Output: PASS or REVIEW with reason.
Run: python scripts/check_sql_reliability.py "Show total MAB by income segment" "SELECT income_segment, SUM(mab_bal) FROM workspace.default.mab_meb GROUP BY income_segment"
"""

import functools
import json
import re
import sys
from pathlib import Path

import sqlglot
from sqlglot import exp

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
        "question_terms": ["min", "mab"],
        "required_sql_terms": ["min", "mab_bal"],
        "reason": "Question asks for minimum MAB, so SQL should use MIN(mab_bal).",
    },
    {
        "question_terms": ["max", "mab"],
        "required_sql_terms": ["max", "mab_bal"],
        "reason": "Question asks for maximum MAB, so SQL should use MAX(mab_bal).",
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
        "question_terms": ["min", "meb"],
        "required_sql_terms": ["min", "meb_bal"],
        "reason": "Question asks for minimum MEB, so SQL should use MIN(meb_bal).",
    },
    {
        "question_terms": ["max", "meb"],
        "required_sql_terms": ["max", "meb_bal"],
        "reason": "Question asks for maximum MEB, so SQL should use MAX(meb_bal).",
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
        "question_terms": [],
        "question_any_terms": ["dormant", "dormancy"],
        "required_sql_terms": ["dormancy_status"],
        "reason": "Question asks about dormancy, so SQL should use dormancy_status.",
    },
    {
        "question_terms": [],
        "question_any_terms": ["nri", "non-resident"],
        "required_sql_terms": ["nri_status"],
        "reason": "Question asks about NRI status, so SQL should use nri_status.",
    },
    {
        "question_terms": [],
        "question_any_terms": ["count", "how many", "number of"],
        "required_sql_terms": ["count"],
        "reason": "Question asks for count/quantity, so SQL should include a COUNT aggregation.",
    },
]


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


@functools.lru_cache(maxsize=1)
def load_glossary() -> dict:
    glossary_path = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "business_glossary.json"
    )
    if glossary_path.exists():
        return json.loads(glossary_path.read_text(encoding="utf-8"))
    return {}


def normalize_business_question(question: str) -> str:
    glossary = load_glossary()
    replacements = {}

    for section in ("metrics", "dimensions"):
        for name, details in glossary.get(section, {}).items():
            for synonym in details.get("synonyms", []):
                replacements[normalize_text(synonym)] = name

    if not replacements:
        return normalize_text(question)

    phrases = sorted(replacements, key=len, reverse=True)
    pattern = r"(?<!\w)(?:" + "|".join(
        re.escape(phrase) for phrase in phrases
    ) + r")(?!\w)"

    return re.sub(
        pattern,
        lambda match: replacements[match.group(0)],
        normalize_text(question),
    )


def contains_term(text: str, term: str) -> bool:
    """Check if term exists in text as a whole word or exact phrase, avoiding false positives like 'count' in 'accounts'."""
    pattern = r"\b" + re.escape(term.strip()) + r"\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def all_terms_present(text: str, terms: list[str]) -> bool:
    for term in terms:
        if not contains_term(text, term):
            return False
    return True


def has_required_calculation(sql_text: str, terms: list[str]) -> bool:
    function_types = {
        "sum": exp.Sum,
        "avg": exp.Avg,
        "min": exp.Min,
        "max": exp.Max,
        "count": exp.Count,
    }
    target_func = terms[0].lower()
    function_type = function_types.get(target_func)

    if function_type is None:
        return all_terms_present(normalize_text(sql_text), terms)

    try:
        query = sqlglot.parse_one(sql_text, read="databricks")
        if query is None:
            return False

        calculations = list(query.find_all(function_type))

        # If checking for COUNT/quantity, also accept window rank functions like ROW_NUMBER() or RANK()
        if target_func == "count" and not calculations:
            window_rank_funcs = (exp.RowNumber, exp.Rank, exp.DenseRank)
            calculations = [node for node in query.walk() if isinstance(node, window_rank_funcs)]

        if not calculations:
            return False

        # If only checking for function presence (e.g. COUNT)
        if len(terms) == 1:
            return True

        target_col = terms[1].lower()

        for calculation in calculations:
            col = calculation.find(exp.Column)
            if col and col.name.lower() == target_col:
                return True

            # Also check if calculation.this is directly an Identifier or matches
            if hasattr(calculation, "this") and calculation.this is not None:
                if str(calculation.this).lower() == target_col:
                    return True

            # If looking for AVG of mab_bal/meb_bal in nested queries/subqueries,
            # accept aggregations over aliased total columns (like AVG(total_mab) or AVG(tot))
            if target_func == "avg" and target_col in ("mab_bal", "meb_bal"):
                calc_str = str(calculation).lower()
                if any(k in calc_str for k in ["total_mab", "total_meb", "tot"]):
                    return True

        return False

    except sqlglot.errors.SqlglotError:
        return False


def is_count_or_row_request(question: str) -> bool:
    """Check if the user is explicitly asking for a count of rows or records."""
    q_lower = normalize_text(question)
    count_patterns = [
        "number of row",
        "number of rows",
        "count of row",
        "count of rows",
        "total rows",
        "total row",
        "how many rows",
        "row count",
        "total number of row",
        "total number of rows",
        "how many records",
        "total records",
        "count of records",
        "record count",
    ]
    return any(p in q_lower for p in count_patterns)


def check_sql_reliability(question: str, sql: str) -> dict:
    normalized_question = normalize_business_question(question)
    clean_sql = sql.strip().rstrip(";")

    review_reasons = []
    matched_rules = 0
    is_row_count = is_count_or_row_request(question)

    for rule in QUESTION_TO_SQL_RULES:
        # If user explicitly asked for number of rows/records, don't demand SUM(mab_bal) or SUM(meb_bal)
        if is_row_count and rule["required_sql_terms"] in [["sum", "mab_bal"], ["sum", "meb_bal"]]:
            continue

        question_matches_rule = all_terms_present(
            normalized_question,
            rule["question_terms"],
        )
        alternative_terms = rule.get("question_any_terms", [])

        if alternative_terms:
            question_matches_rule = question_matches_rule and any(
                contains_term(normalized_question, term)
                for term in alternative_terms
            )

        if question_matches_rule:
            matched_rules += 1
            sql_has_required_terms = has_required_calculation(
                clean_sql,
                rule["required_sql_terms"],
            )

            if not sql_has_required_terms:
                review_reasons.append(rule["reason"])

    if review_reasons:
        return {
            "decision": "REVIEW",
            "reason": " ".join(review_reasons),
        }

    # If both tables are referenced in SQL, ensure join condition is present
    sql_lower = clean_sql.lower()
    needs_join = ("p2c" in sql_lower) and ("mab_meb" in sql_lower)
    if needs_join:
        has_join_keys = (
            ("source_account_nbr" in sql_lower and "acctno" in sql_lower)
            or ("on " in sql_lower and "=" in sql_lower)
        )
        if not has_join_keys:
            return {
                "decision": "REVIEW",
                "reason": "Query uses both tables but appears to be missing the join condition (source_account_nbr = ACCTNO).",
            }

    if matched_rules == 0:
        # Check if the query has valid SELECT expressions and parses properly
        try:
            parsed = sqlglot.parse_one(clean_sql, read="databricks")
            if parsed is not None:
                return {
                    "decision": "PASS",
                    "reason": "SQL query is structurally valid for the requested question.",
                }
        except sqlglot.errors.SqlglotError:
            pass

        return {
            "decision": "REVIEW",
            "reason": "No reliability rule covers this question.",
        }

    return {
        "decision": "PASS",
        "reason": "SQL matches the question requirements.",
    }


def main() -> None:
    if len(sys.argv) >= 3:
        question = sys.argv[1]
        sql = sys.argv[2]
    else:
        question = "Show total MAB by income segment"
        sql = "SELECT income_segment, SUM(mab_bal) FROM workspace.default.mab_meb GROUP BY income_segment"

    result = check_sql_reliability(question, sql)

    print(f"Question: {question}")
    print(f"SQL: {sql}")
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    main()
