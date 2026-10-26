"""
Step 22: Ask an analytics question.
Purpose: Generate SQL, check it, and request execution approval.
Input: An English question entered in the terminal.
Output: Proposed SQL, check decisions, and optional database rows.
Run: python scripts/ask_question.py
"""

from generate_sql_with_llm import generate_sql
from check_sql_safety import check_sql_safety
from check_sql_reliability import check_sql_reliability
from run_verified_sql import run_verified_sql


def main() -> None:
    question = input("Your question: ").strip()
    if not question:
        print("Please enter a question.")
        return

    sql_text = generate_sql(question)
    print(f"\nProposed SQL:\n{sql_text}")

    if sql_text == "Not under my knowledge.":
        return

    safety = check_sql_safety(sql_text)
    print(f"\nSafety: {safety['decision']} - {safety['reason']}")
    if safety["decision"] != "ALLOW":
        return

    reliability = check_sql_reliability(question, sql_text)
    print(f"Reliability: {reliability['decision']} - {reliability['reason']}")
    if reliability["decision"] != "PASS":
        return

    print("\nChecks are limited. Review the SQL before approving.")
    approval = input("Type RUN to execute, or press Enter to cancel: ")
    if approval.strip() != "RUN":
        print("Cancelled. No SQL was executed.")
        return

    result = run_verified_sql(question, sql_text)
    print(f"\nDecision: {result['decision']} - {result['reason']}")
    if result["decision"] != "ALLOW":
        return

    if not result["rows"]:
        print("Query returned no rows.")
    else:
        print("Results: up to 20 rows, possibly incomplete.")
        for row in result["rows"]:
            print(row)


if __name__ == "__main__":
    main()