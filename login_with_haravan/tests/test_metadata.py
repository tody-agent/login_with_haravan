import re
import tomllib
import unittest
from pathlib import Path

import login_with_haravan


ROOT = Path(__file__).resolve().parents[2]


class PackageMetadataTest(unittest.TestCase):
    def test_package_versions_are_consistent(self):
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
        setup_py = (ROOT / "setup.py").read_text()
        hooks_py = (ROOT / "login_with_haravan" / "hooks.py").read_text()

        setup_version = re.search(r'version="([^"]+)"', setup_py)
        hooks_version = re.search(r'app_version = "([^"]+)"', hooks_py)

        self.assertIsNotNone(setup_version)
        self.assertIsNotNone(hooks_version)
        self.assertEqual(login_with_haravan.__version__, pyproject["project"]["version"])
        self.assertEqual(login_with_haravan.__version__, setup_version.group(1))
        self.assertEqual(login_with_haravan.__version__, hooks_version.group(1))


if __name__ == "__main__":
    unittest.main()
