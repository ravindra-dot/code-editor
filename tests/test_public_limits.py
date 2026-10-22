import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app as app_module
import limits


class PublicLimitTests(unittest.TestCase):
    def test_per_client_window_and_rollover(self):
        with patch.object(limits.time, "monotonic", return_value=100):
            self.assertTrue(limits.allow("test-client", "test-category", 2))
            self.assertTrue(limits.allow("test-client", "test-category", 2))
            self.assertFalse(limits.allow("test-client", "test-category", 2))
            self.assertTrue(limits.allow("other-client", "test-category", 2))
        with patch.object(limits.time, "monotonic", return_value=161):
            self.assertTrue(limits.allow("test-client", "test-category", 2))

    def test_public_mode_rejects_cross_site_post(self):
        app_module.app.config["TESTING"] = True
        with patch.object(app_module, "PUBLIC_MODE", True):
            response = app_module.app.test_client().post(
                "/run",
                json={"language": "python", "code": "print(1)", "input": ""},
                headers={"Origin": "https://other.example"},
            )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
