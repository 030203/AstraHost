import json
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT_DIR / "tests" / "fixtures" / "skill_routing_cases.json"


class SkillRoutingFixtureShapeTest(unittest.TestCase):
    def test_fixture_cases_have_required_fields(self):
        with FIXTURE_PATH.open("r", encoding="utf-8") as file:
            cases = json.load(file)

        self.assertIsInstance(cases, list)
        self.assertGreaterEqual(len(cases), 10)

        seen_ids = set()
        for case in cases:
            self.assertIsInstance(case.get("id"), str)
            self.assertTrue(case["id"])
            self.assertNotIn(case["id"], seen_ids)
            seen_ids.add(case["id"])

            self.assertIsInstance(case.get("message"), str)
            self.assertTrue(case["message"].strip())
            self.assertIsInstance(case.get("allowed_tools"), list)
            self.assertIsInstance(case.get("expected_skills"), list)
            self.assertIsInstance(case.get("expected_tools"), list)
            self.assertIsInstance(case.get("category"), str)
            self.assertIsInstance(case.get("should_call_tools"), bool)


if __name__ == "__main__":
    unittest.main()
