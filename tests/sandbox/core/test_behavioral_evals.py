import json
import tempfile
import unittest
from pathlib import Path

import evals_pipeline


class BehavioralEvalPipelineTests(unittest.TestCase):
    def test_manifest_covers_every_required_side_effect(self):
        cases = evals_pipeline.load_manifest()
        self.assertTrue(evals_pipeline.REQUIRED_EFFECTS.issubset({case["effect"] for case in cases}))
        self.assertTrue(all("expected_reviewer_action" not in case for case in cases))

    def test_incomplete_or_duplicate_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps({"cases": [{
                "id": "one", "effect": "filesystem_side_effect",
                "assertion": "assert", "test": "test.name",
            }]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing effects"):
                evals_pipeline.load_manifest(path)


if __name__ == "__main__":
    unittest.main()
