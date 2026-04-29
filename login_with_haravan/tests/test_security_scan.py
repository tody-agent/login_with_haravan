import unittest
import os
import re
import subprocess

class TestSecurityScan(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

    def test_no_secret_files_tracked(self):
        """Ensure no secret files (.env, site_config.json) are tracked by git."""
        try:
            tracked_files = subprocess.check_output(
                ["git", "ls-files"],
                cwd=self.repo_root,
                encoding="utf-8"
            ).splitlines()
        except subprocess.CalledProcessError:
            self.skipTest("Not a git repository or git not found.")

        bad_files = [".env", ".dev.vars", ".env.local", "site_config.json"]
        found = [f for f in bad_files if f in tracked_files]
        self.assertEqual(found, [], f"Secret files tracked by git: {', '.join(found)}")

    def test_gitignore_contains_security_patterns(self):
        """Ensure .gitignore protects common secrets."""
        gitignore_path = os.path.join(self.repo_root, ".gitignore")
        if not os.path.exists(gitignore_path):
            self.fail(".gitignore file is missing!")

        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("site_config.json", content, ".gitignore missing site_config.json")
        # Check standard python ignores
        self.assertIn("__pycache__", content, ".gitignore missing __pycache__")

    def test_no_hardcoded_secrets_in_source(self):
        """Scan source code for potentially hardcoded secrets."""
        dangerous_patterns = [
            re.compile(r"SERVICE_KEY\s*[=:]\s*['\"][a-zA-Z0-9/+=]{20,}['\"]"),
            re.compile(r"PRIVATE_KEY\s*[=:]\s*['\"][a-zA-Z0-9/+=]{20,}['\"]"),
            re.compile(r"client_secret\s*[=:]\s*['\"][a-zA-Z0-9/+=]{20,}['\"]"),
            re.compile(r"-----BEGIN.*PRIVATE KEY-----")
        ]

        src_dir = os.path.join(self.repo_root, "login_with_haravan")
        for root, dirs, files in os.walk(src_dir):
            # Skip test files and cache
            if "tests" in root or "__pycache__" in root:
                continue

            for file in files:
                if not file.endswith((".py", ".js")):
                    continue

                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                for pattern in dangerous_patterns:
                    match = pattern.search(content)
                    self.assertIsNone(
                        match,
                        f"{file} contains potential hardcoded secret at: {match.group(0) if match else ''}"
                    )
