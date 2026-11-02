import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_sql_reliability import check_sql_reliability


class SqlReliabilityTests(unittest.TestCase):
    def test_total_mab_matching(self):
        sql = "SELECT income_segment, SUM(mab_bal) FROM workspace.default.mab_meb GROUP BY income_segment"
        result = check_sql_reliability("Show total MAB by income segment", sql)
        self.assertEqual(result["decision"], "PASS")

    def test_avg_mab_mismatch(self):
        sql = "SELECT income_segment, AVG(mab_bal) FROM workspace.default.mab_meb GROUP BY income_segment"
        result = check_sql_reliability("Show total MAB by income segment", sql)
        self.assertEqual(result["decision"], "REVIEW")
        self.assertIn("SUM(mab_bal)", result["reason"])

    def test_count_accounts_matching(self):
        sql = "SELECT product_type, COUNT(*) AS account_count FROM workspace.default.p2c GROUP BY product_type"
        result = check_sql_reliability("How many accounts by product type?", sql)
        self.assertEqual(result["decision"], "PASS")

    def test_dormancy_rule(self):
        sql = "SELECT product_type, dormancy_status, COUNT(*) FROM workspace.default.p2c GROUP BY product_type, dormancy_status"
        result = check_sql_reliability("Show dormant accounts by product type", sql)
        self.assertEqual(result["decision"], "PASS")

    def test_missing_join_detected(self):
        # Referencing both tables without join keys
        sql = "SELECT p.product_type, m.mab_bal FROM workspace.default.p2c p, workspace.default.mab_meb m"
        result = check_sql_reliability("Show balances and product types", sql)
        self.assertEqual(result["decision"], "REVIEW")
        self.assertIn("join condition", result["reason"].lower())

    def test_synonym_normalization(self):
        # "monthly average balance" should normalize to MAB and require SUM(mab_bal)
        sql = "SELECT SUM(mab_bal) FROM workspace.default.mab_meb"
        result = check_sql_reliability("Show total monthly average balance", sql)
        self.assertEqual(result["decision"], "PASS")

    def test_row_count_not_flagged_as_balance_sum(self):
        sql = "SELECT COUNT(ACCTNO) AS total_rows FROM workspace.default.mab_meb"
        result = check_sql_reliability("give me total number of row in meb", sql)
        self.assertEqual(result["decision"], "PASS")
