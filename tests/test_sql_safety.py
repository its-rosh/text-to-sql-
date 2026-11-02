import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_sql_safety import check_sql_safety


class SqlSafetyTests(unittest.TestCase):
    def test_basic_select_allowed(self):
        result = check_sql_safety("SELECT product_type FROM workspace.default.p2c")
        self.assertEqual(result["decision"], "ALLOW")

    def test_catalog_table_allowed(self):
        result = check_sql_safety("SELECT product_type FROM cdp_uat.dsag_new.p2c")
        self.assertEqual(result["decision"], "ALLOW")

    def test_unqualified_table_allowed(self):
        result = check_sql_safety("SELECT product_type FROM p2c")
        self.assertEqual(result["decision"], "ALLOW")

    def test_ddl_dml_blocked(self):
        bad_queries = [
            "DELETE FROM workspace.default.p2c",
            "DROP TABLE workspace.default.p2c",
            "UPDATE workspace.default.p2c SET product_type = 'SA'",
            "INSERT INTO workspace.default.p2c VALUES ('1', '2')",
            "TRUNCATE TABLE workspace.default.p2c",
            "CREATE TABLE evil AS SELECT 1",
            "ALTER TABLE workspace.default.p2c ADD COLUMN evil STRING",
        ]
        for query in bad_queries:
            with self.subTest(query=query):
                result = check_sql_safety(query)
                self.assertEqual(result["decision"], "BLOCK")

    def test_direct_star_blocked(self):
        result = check_sql_safety("SELECT * FROM workspace.default.p2c")
        self.assertEqual(result["decision"], "BLOCK")

    def test_unapproved_table_blocked(self):
        result = check_sql_safety("SELECT secret FROM malicious_db.passwords")
        self.assertEqual(result["decision"], "BLOCK")

    def test_multiple_statements_blocked(self):
        result = check_sql_safety("SELECT 1 FROM workspace.default.p2c; DROP TABLE workspace.default.p2c")
        self.assertEqual(result["decision"], "BLOCK")

    def test_count_star_allowed(self):
        result = check_sql_safety("SELECT COUNT(*) FROM workspace.default.p2c")
        self.assertEqual(result["decision"], "ALLOW")

    def test_benchmark_prompt1_cte_safety(self):
        # Benchmark 1 uses CTEs
        sql = """
        WITH joined AS (
            SELECT p.ucic_value, p.source_account_nbr, p.account_open_date, p.dormancy_status, m.mab_bal
            FROM workspace.default.p2c p
            INNER JOIN workspace.default.mab_meb m ON p.source_account_nbr = m.ACCTNO
        ),
        aged AS (
            SELECT *, CASE WHEN dormancy_status = 'D' THEN 1 ELSE 0 END AS is_dormant
            FROM joined
        )
        SELECT is_dormant, SUM(mab_bal) AS total_mab FROM aged GROUP BY is_dormant
        """
        result = check_sql_safety(sql)
        self.assertEqual(result["decision"], "ALLOW")
