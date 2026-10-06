"""
Step 11: Check SQL Safety
Purpose: Allow only read-only SELECT SQL before database execution.
Input: SQL text from terminal.
Output: ALLOW or BLOCK with reason.
Run: python scripts/check_sql_safety.py "SELECT * FROM p2c"
"""

import sys


BLOCKED_KEYWORDS = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "merge",
    "replace",
]


APPROVED_TABLES = [
    "p2c",
    "mab_meb",
    "cdp_uat.dsag_new.p2c",
    "cdp_uat.dsag_new.mab_meb",
]


def normalize_sql(sql: str) -> str:
    return " ".join(sql.lower().split())


def starts_with_allowed_keyword(normalized_sql: str) -> bool:
    return normalized_sql.startswith("select ") or normalized_sql.startswith("with ")


def has_blocked_keyword(normalized_sql: str) -> bool:
    words = normalized_sql.replace(";", " ").split()

    for keyword in BLOCKED_KEYWORDS:
        if keyword in words:
            return True

    return False


def has_only_one_statement(sql: str) -> bool:
    statements = [part.strip() for part in sql.split(";") if part.strip()]

    return len(statements) <= 1


def uses_approved_table(normalized_sql: str) -> bool:
    for table in APPROVED_TABLES:
        if table.lower() in normalized_sql:
            return True

    return False


def check_sql_safety(sql: str) -> dict:
    normalized_sql = normalize_sql(sql)

    if not has_only_one_statement(sql):
        return {
            "decision": "BLOCK",
            "reason": "SQL contains more than one statement.",
        }

    if not starts_with_allowed_keyword(normalized_sql):
        return {
            "decision": "BLOCK",
            "reason": "SQL must start with SELECT or WITH.",
        }

    if has_blocked_keyword(normalized_sql):
        return {
            "decision": "BLOCK",
            "reason": "SQL contains a blocked keyword.",
        }

    if not uses_approved_table(normalized_sql):
        return {
            "decision": "BLOCK",
            "reason": "SQL does not use an approved project table.",
        }

    return {
        "decision": "ALLOW",
        "reason": "SQL passed read-only safety checks.",
    }


def main() -> None:
    if len(sys.argv) > 1:
        sql = " ".join(sys.argv[1:])
    else:
        sql = "SELECT product_type, COUNT(*) FROM p2c GROUP BY product_type"

    result = check_sql_safety(sql)

    print(f"SQL: {sql}")
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    main()