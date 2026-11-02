"""
Step 22: Ask an analytics question.
Purpose: Generate SQL, check it, and request execution approval.
Input: An English question entered in the terminal or passed as CLI arguments.
Output: Proposed SQL, check decisions, and database rows.
Run: python scripts/ask_question.py "Show total MAB by income segment"
"""

import sys
import pandas as pd
from generate_sql_with_llm import generate_sql
from check_sql_safety import check_sql_safety
from check_sql_reliability import check_sql_reliability
from run_verified_sql import run_verified_sql


def main() -> None:
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    local_mode = "--local" in sys.argv

    if args:
        question = " ".join(args).strip()
        print(f"Question: {question}")
    else:
        question = input("Your question: ").strip()

    if not question:
        print("Please enter a question.")
        return

    print("\n[1/4] Generating SQL...")
    sql_text = generate_sql(question)
    print(f"\nProposed SQL:\n{sql_text}\n")

    if sql_text == "Not under my knowledge.":
        print("The chatbot does not have approved context to answer this question.")
        return

    print("[2/4] Safety check...")
    safety = check_sql_safety(sql_text)
    print(f"Safety: {safety['decision']} - {safety['reason']}")
    if safety["decision"] != "ALLOW":
        print("Execution blocked by safety policy.")
        return

    print("\n[3/4] Reliability check...")
    reliability = check_sql_reliability(question, sql_text)
    print(f"Reliability: {reliability['decision']} - {reliability['reason']}")
    if reliability["decision"] != "PASS":
        print("Query needs review before execution.")
        return

    print("\n[4/4] Execution Approval:")
    print("Checks are limited. Review the SQL before approving.")
    approval = input("Type RUN to execute, or press Enter to cancel: ")
    if approval.strip().upper() != "RUN":
        print("Cancelled. No SQL was executed.")
        return

    result = run_verified_sql(question, sql_text)
    print(f"\nExecution: {result['decision']} ({result.get('source', 'unknown')})")
    print(f"Reason: {result['reason']}\n")

    if result["decision"] != "ALLOW":
        return

    if not result["rows"]:
        print("Query returned no rows.")
    else:
        row_dicts = [r.asDict() if hasattr(r, "asDict") else r for r in result["rows"]]
        df = pd.DataFrame(row_dicts)
        print(f"Results (showing {len(df)} rows):")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
