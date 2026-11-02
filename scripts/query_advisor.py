"""
Centralized Query Advisor & Error Diagnostic Helper
Purpose: Provide clear, plain-language error explanations, actionable suggestions,
         and explicit "Suggested change in query" examples so users can easily
         rectify their queries in one go.
"""

import re


def get_query_advice(stage: str, decision: str, reason: str, question: str = "", sql: str = "") -> dict:
    """
    Analyzes error / review state and returns:
    {
        "title": Short title,
        "summary": Plain English explanation of what went wrong,
        "suggested_query": Concrete recommended question phrasing to copy-paste,
        "tips": List of actionable suggestions / alternative prompts the user can try
    }
    """
    reason_lower = (reason or "").lower()
    q_lower = (question or "").lower()

    # 1. OUT OF SCOPE / TOPIC NOT RECOGNIZED IN PRE-CHECK
    if stage == "pre_check" or "not match known project data" in reason_lower or "out of scope" in reason_lower or "out_of_scope" in reason_lower:
        # Detect if user was asking about accounts opened/closed
        if any(w in q_lower for w in ["opened", "open date", "opening"]):
            suggested_q = "How many accounts were opened in each year? Show the latest year first."
        elif any(w in q_lower for w in ["closed", "close date", "closure"]):
            suggested_q = "How many closed accounts are there per product type?"
        elif any(w in q_lower for w in ["dormant", "dormancy"]):
            suggested_q = "Show the count of accounts by dormancy status."
        elif any(w in q_lower for w in ["balance", "mab", "meb"]):
            suggested_q = "Show total MAB by income segment."
        else:
            suggested_q = "Show total MAB by income segment"

        return {
            "title": "Topic or Phrasing Not Recognized",
            "summary": "The system could not match your question with approved banking tables (p2c for accounts/dates/dormancy and mab_meb for balances).",
            "suggested_query": suggested_q,
            "tips": [
                "**p2c table:** Account numbers, opening/closing dates, dormancy status ('D'/'A'/'I'), product types (SA, CA, FD, RD, LN, CC, OD), NRI status.",
                "**mab_meb table:** Monthly Average Balance (MAB), Month-End Balance (MEB), income tier, final customer segment.",
                "👉 Try using standard phrases like 'How many accounts were opened...', 'Show total balance by...', or 'Count of accounts by...'"
            ]
        }

    # 2. MISSING CONTEXT / WEAK EVIDENCE
    if "evidence" in reason_lower or "context" in reason_lower:
        return {
            "title": "Need More Information in Question",
            "summary": "The chatbot could not find enough metadata evidence to safely answer this question.",
            "suggested_query": "What is the average MAB balance for active savings accounts?",
            "tips": [
                "Be more specific with the business terms (e.g. mention 'MAB balance', 'MEB balance', 'dormancy', or 'product type')."
            ]
        }

    # 3. SAFETY GATE - BLOCKED SQL (DDL / DML / Injection)
    if stage == "safety":
        return {
            "title": "Safety Gate Blocked This Query",
            "summary": "The system only permits read-only SELECT queries. Modifying, creating, or deleting records or tables is strictly prevented.",
            "suggested_query": "Show total MAB by income segment",
            "tips": [
                "Remove any keywords like INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or multiple semicolon-separated statements.",
                "Phrase your request purely to view or aggregate data (e.g., 'Show...', 'List...', 'Find the average...')."
            ]
        }

    # 4. RELIABILITY GATE - REVIEW
    if stage == "reliability" or decision == "REVIEW":
        # Case A: MEB / MAB balance vs Count confusion
        if "sum(meb_bal)" in reason_lower or "sum(mab_bal)" in reason_lower:
            return {
                "title": "Calculation Ambiguity Detected",
                "summary": "Your question mentioned balance terms (MAB/MEB), but the query calculation might not match your intent.",
                "suggested_query": "Show total MEB balance by income segment" if "meb" in q_lower else "Show total MAB by income segment",
                "tips": [
                    "If you wanted the **count of records / accounts**: Try asking *'Show number of accounts in MEB'*.",
                    "If you wanted the **sum of money / balance**: Try asking *'Show total MEB balance'*."
                ]
            }

        # Case B: Missing Average / Minimum / Maximum aggregation
        if any(agg in reason_lower for agg in ["avg(", "min(", "max("]):
            return {
                "title": "Missing Requested Aggregation",
                "summary": "You asked for an average, minimum, or maximum, but the generated SQL does not calculate it.",
                "suggested_query": "Show average MAB and MEB by GL description for retail accounts.",
                "tips": [
                    "Specify the target metric clearly: e.g. *'Show average MAB balance'* or *'Show minimum MEB balance by income segment'*."
                ]
            }

        # Case C: Missing Segment / Grouping Dimension
        if any(dim in reason_lower for dim in ["income_segment", "final_segment", "product_type", "dormancy_status", "nri_status"]):
            return {
                "title": "Missing Breakdown / Category Grouping",
                "summary": "The query needs to group results by the category you asked for.",
                "suggested_query": "Show total MAB grouped by income segment",
                "tips": [
                    "Explicitly state the grouping: *'Show total balance grouped by income segment'* or *'Show account count grouped by product type'*."
                ]
            }

        # Case D: Missing join
        if "join" in reason_lower:
            return {
                "title": "Missing Table Relationship",
                "summary": "The query references both accounts and balances but is missing the link between them.",
                "suggested_query": "For active, NRI customers, show number of accounts and total MAB by product type, highest MAB first.",
                "tips": [
                    "Both tables link on account number (`source_account_nbr = ACCTNO`)."
                ]
            }

        # General reliability fallback
        return {
            "title": "Query Requires Review",
            "summary": reason,
            "suggested_query": "Show total MAB by income segment",
            "tips": [
                "Check the proposed SQL query above to ensure it calculates what you intended.",
                "If it looks right to you, you can still execute it using the **Execute with Caution** button below."
            ]
        }

    # 5. EXECUTION ERROR (Syntax / Runtime)
    if stage == "execution":
        return {
            "title": "Query Execution Failed",
            "summary": f"The database engine could not execute the SQL: {reason}",
            "suggested_query": "Show total MAB by income segment",
            "tips": [
                "Check that function names match Databricks SQL standards (e.g. `DATEDIFF()` instead of SQLite-specific functions).",
                "Avoid unsupported syntax or non-existent column names.",
                "Try selecting one of the benchmark questions from the dropdown to see working query structures."
            ]
        }

    return {
        "title": "Suggestion",
        "summary": reason,
        "suggested_query": "Show total MAB by income segment",
        "tips": ["Try phrasing your question using simple, standard banking terms."]
    }
