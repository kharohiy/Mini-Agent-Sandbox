import unittest

from runner import parse_reviewer_decision


class ReviewerDecisionTests(unittest.TestCase):
    def test_accepts_exact_structured_approval(self):
        self.assertEqual(parse_reviewer_decision('{"decision":"APPROVE"}'), "APPROVE")

    def test_accepts_structured_rejection_with_reason(self):
        self.assertEqual(
            parse_reviewer_decision('{"decision":"REJECTED","reason":"Missing tests"}'),
            "REJECTED",
        )

    def test_rejects_approval_substring_in_plain_text(self):
        self.assertIsNone(parse_reviewer_decision("DO NOT APPROVE this change."))

    def test_rejects_non_json_approval(self):
        self.assertIsNone(parse_reviewer_decision("APPROVE"))

    def test_rejects_unknown_decision(self):
        self.assertIsNone(parse_reviewer_decision('{"decision":"MAYBE"}'))


if __name__ == "__main__":
    unittest.main()
