import unittest

from patch_policy import validate_unified_diff


def diff(old, new=None):
    new = old if new is None else new
    old_header = "a/" + old if old else "/dev/null"
    new_header = "b/" + new if new else "/dev/null"
    git_old = old or new
    git_new = new or old
    return (
        f"diff --git a/{git_old} b/{git_new}\n"
        f"--- {old_header}\n+++ {new_header}\n"
        "@@ -1 +1 @@\n-before\n+after\n"
    )


class PatchPolicyTests(unittest.TestCase):
    def test_accepts_declared_text_patch(self):
        self.assertEqual(validate_unified_diff(diff("app/Main.kt"), ["app/Main.kt"]), ["app/Main.kt"])

    def test_accepts_creation_when_new_path_is_declared(self):
        self.assertEqual(validate_unified_diff(diff(None, "app/New.kt"), ["app/New.kt"]), ["app/New.kt"])

    def test_rejects_out_of_scope_and_traversal_paths(self):
        with self.assertRaises(ValueError):
            validate_unified_diff(diff("app/Other.kt"), ["app/Main.kt"])
        with self.assertRaises(ValueError):
            validate_unified_diff(diff("../outside.kt"), ["../outside.kt"])

    def test_rejects_protected_binary_and_non_diff_content(self):
        for text, declared in (
            (diff(".vault/secret.kt"), [".vault/secret.kt"]),
            ("GIT binary patch\n", ["app/Main.kt"]),
            ("APPROVE\n", ["app/Main.kt"]),
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_unified_diff(text, declared)


if __name__ == "__main__":
    unittest.main()
