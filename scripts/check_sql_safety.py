"""
Step 11: Check SQL Safety.
Purpose: Check query structure, approved tables, and wildcard columns.
Input: SQL text passed through the terminal or API.
Output: ALLOW or BLOCK with a reason.
Run: python scripts/check_sql_safety.py "SELECT product_type FROM workspace.default.p2c"
"""

import os
import sys
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from dotenv import load_dotenv

load_dotenv()


def get_approved_tables() -> set[str]:
    tables = {
        "workspace.default.p2c",
        "workspace.default.mab_meb",
        "cdp_uat.dsag_new.p2c",
        "cdp_uat.dsag_new.mab_meb",
        "default.p2c",
        "default.mab_meb",
        "p2c",
        "mab_meb",
    }
    p2c_env = os.getenv("DATABRICKS_P2C_TABLE")
    if p2c_env:
        tables.add(p2c_env.strip().lower())
    mab_env = os.getenv("DATABRICKS_MAB_MEB_TABLE")
    if mab_env:
        tables.add(mab_env.strip().lower())
    return tables


APPROVED_TABLES = get_approved_tables()


def check_sql_safety(sql_text: str) -> dict:
    def block(reason: str) -> dict:
        return {"decision": "BLOCK", "reason": reason}

    if not sql_text or not sql_text.strip():
        return block("Empty SQL query.")

    clean_sql = sql_text.strip().rstrip(";")

    try:
        statements = sqlglot.parse(clean_sql, read="databricks")

        if len(statements) != 1 or statements[0] is None:
            return block("Provide exactly one SQL statement.")

        query = statements[0]

        # A SELECT with WITH clauses also has a Select root.
        if not isinstance(query, exp.Select):
            return block("Only SELECT queries are allowed.")

        for node in query.walk():
            if isinstance(node, (exp.DDL, exp.DML, exp.Command, exp.Into)):
                return block("Database-changing SQL is not allowed.")

        # Check for wildcards directly on physical database tables
        for scope in traverse_scope(query):
            has_star = False
            if hasattr(scope.expression, "selects"):
                has_star = any(col.is_star for col in scope.expression.selects)
            elif isinstance(scope.expression, exp.Select):
                has_star = any(col.is_star for col in scope.expression.expressions)

            if has_star:
                for _, (_, source) in scope.selected_sources.items():
                    if isinstance(source, exp.Table):
                        return block("SELECT * and table.* on physical tables are not allowed.")

        found_table = False
        approved_tables = get_approved_tables()

        # Scopes distinguish actual database tables from CTE references.
        for scope in traverse_scope(query):
            for _, source in scope.selected_sources.values():
                if not isinstance(source, exp.Table):
                    continue

                if not all(
                    isinstance(part, exp.Identifier)
                    for part in source.parts
                ):
                    return block("Only explicitly named tables are allowed.")

                table_name = ".".join(
                    part.name for part in source.parts
                ).lower()

                if table_name not in approved_tables:
                    return block(f"Table is not approved: {table_name}")

                found_table = True

        if not found_table:
            return block("Query must use an approved project table.")

    except sqlglot.errors.SqlglotError:
        return block("SQL could not be parsed or checked.")

    return {
        "decision": "ALLOW",
        "reason": "SQL passed the implemented structural checks.",
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Pass a SQL query inside double quotes.")
        return

    sql_text = " ".join(sys.argv[1:])
    result = check_sql_safety(sql_text)

    print(f"SQL: {sql_text}")
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    main()
