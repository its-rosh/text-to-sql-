import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_age_bucket_report import get_age_bucket_sql

class TestAgeBucketSQL(unittest.TestCase):
    def test_sql_contains_required_parts(self):
        sql = get_age_bucket_sql()
        # Basic sanity checks
        self.assertIn('FROM cdp_uat.dsag_new.p2c', sql)
        self.assertIn('INNER JOIN cdp_uat.dsag_new.mab_meb', sql)
        self.assertIn('age_bucket', sql)
        self.assertIn('risk_flag', sql)
        self.assertIn("open_status = 'Open'", sql)  # ensure open/closed logic
        # Ensure ONLY SELECT is used (no INSERT/UPDATE)
        self.assertNotRegex(sql, r'\bINSERT\b|\bUPDATE\b|\bDELETE\b')

if __name__ == '__main__':
    unittest.main()
