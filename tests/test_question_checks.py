"""
Step 21: Test question checks.
Purpose: Verify missing evidence stops the pipeline.
Input: Simulated retrieval results.
Output: Test success or failure, without external services.
Run: python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_rag_evidence import decide_if_evidence_is_enough
from check_ques_before_sql import run_pre_sql_checks
from check_sql_safety import check_sql_safety
from check_sql_reliability import check_sql_reliability


class QuestionChecksTests(unittest.TestCase):
    def test_empty_evidence_is_rejected(self):
        results = {"documents": [[]], "distances": [[]]}
        allowed, reason = decide_if_evidence_is_enough(results)
        self.assertFalse(allowed)
        self.assertIn("No matching", reason)

    def test_missing_metadata_blocks_question(self):
        results = {
            "documents": [["Balance table description"]],
            "distances": [[0.1]],
        }

        with (
            patch(
                "check_ques_before_sql.route_question",
                return_value={"route": "mab_meb"},
            ),
            patch(
                "check_ques_before_sql.retrieve_context",
                return_value=results,
            ),
            patch(
                "check_ques_before_sql.load_metadata_chunks",
                return_value=[],
            ),
        ):
            result = run_pre_sql_checks("Show total MAB")

        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(
            result["final_answer"], "Not under my knowledge."
        )
        self.assertIn("missing", result["reason"].lower())

###Test Weak Evidence

    def test_weak_evidence_is_rejected(self):
        results = {
            "documents": [["Unrelated context"]],
            "distances": [[2.0]],
        }

        allowed, reason = decide_if_evidence_is_enough(results)

        self.assertFalse(allowed)
        self.assertIn("blocked", reason.lower())

###Test Early Stopping

    def test_out_of_scope_skips_retrieval(self):
        with (
            patch(
                "check_ques_before_sql.route_question",
                return_value={
                    "route": "out_of_scope",
                    "reason": "Unsupported question.",
                },
            ),
            patch(
                "check_ques_before_sql.retrieve_context"
            ) as mock_retrieval,
        ):
            result = run_pre_sql_checks("What is the weather?")

        self.assertEqual(result["decision"], "BLOCK")
        mock_retrieval.assert_not_called()

### SQL Safety Tests

    def test_sql_safety_cases(self):
        cases = [
            ("SELECT product_type FROM workspace.default.p2c", "ALLOW"),
            ("DELETE FROM workspace.default.p2c", "BLOCK"),
            ("SELECT * FROM workspace.default.p2c", "BLOCK"),
            ("SELECT product_type FROM workspace.default.other_table", "BLOCK"),
            ("SELECT COUNT(*) FROM workspace.default.p2c", "ALLOW"),
        ]

        for sql_text, expected in cases:
            with self.subTest(sql=sql_text):
                result = check_sql_safety(sql_text)
                self.assertEqual(result["decision"], expected)

### SQL Calculation Tests

    def test_sql_calculation_cases(self):
        cases = [
            ("SUM(mab_bal)", "PASS"),
            ("AVG(mab_bal)", "REVIEW"),
            ("SUM(meb_bal), AVG(mab_bal)", "REVIEW"),
        ]

        for calculation, expected in cases:
            with self.subTest(calculation=calculation):
                sql_text = (
                    f"SELECT {calculation} "
                    "FROM workspace.default.mab_meb"
                )
                result = check_sql_reliability("Show total MAB", sql_text)
                self.assertEqual(result["decision"], expected)