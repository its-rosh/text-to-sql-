import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from route_question import route_question


class RouteQuestionTests(unittest.TestCase):
    def test_mab_meb_routing(self):
        result = route_question("Show total MAB by income segment")
        self.assertEqual(result["route"], "mab_meb")

    def test_p2c_routing(self):
        result = route_question("How many accounts are dormant?")
        self.assertEqual(result["route"], "p2c")

    def test_both_tables_routing(self):
        result = route_question("Show average balance for dormant accounts by product type")
        self.assertEqual(result["route"], "both_tables")

    def test_out_of_scope_routing(self):
        result = route_question("What is the weather in Delhi?")
        self.assertEqual(result["route"], "out_of_scope")

    def test_benchmark_prompt1_routing(self):
        q = (
            "I want to see our accounts grouped by how long they've been open — "
            "like under 2 years, 2 to 5 years, 5 to 10 years, and over 10 years. "
            "For each of those age groups, show me how many accounts are still open "
            "versus already closed, what share have gone dormant, and what the average "
            "and total balances look like."
        )
        result = route_question(q)
        self.assertEqual(result["route"], "both_tables")

    def test_benchmark_prompt2_routing(self):
        q = (
            "For each account type and customer segment, I want to see how many accounts we have, "
            "how many are dormant and what percentage that is, the average and total balances "
            "(both monthly average and month-end)."
        )
        result = route_question(q)
        self.assertEqual(result["route"], "both_tables")
