"""
Step 11: Check SQL Safety.
Purpose: Check query structure, approved tables, and wildcard columns.
Input: SQL text passed through the terminal.
Output: ALLOW or BLOCK with a reason.
Run: python scripts/check_sql_safety.py "SELECT product_type FROM workspace.default.p2c"
"""

import sys
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope


APPROVED_TABLES = {
    "workspace.default.p2c",
    "workspace.default.mab_meb",
}


def check_sql_safety(sql_text: str) -> dict:
    def block(reason: str) -> dict:
        return {"decision": "BLOCK", "reason": reason}

    try:
        # Parse SQL into a structure instead of checking text fragments.
        statements = sqlglot.parse(sql_text, read="databricks")

        if len(statements) != 1 or statements[0] is None:
            return block("Provide exactly one SQL statement.")

        query = statements[0]

        # A SELECT with WITH clauses also has a Select root.
        if not isinstance(query, exp.Select):
            return block("Only SELECT queries are allowed.")

        for node in query.walk():
            if isinstance(node, (exp.DDL, exp.DML, exp.Command, exp.Into)):
                return block("Database-changing SQL is not allowed.")

        for select in query.find_all(exp.Select):
            for column in select.expressions:
                if column.is_star:
                    return block("SELECT * and table.* are not allowed.")

        found_table = False

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

                if table_name not in APPROVED_TABLES:
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