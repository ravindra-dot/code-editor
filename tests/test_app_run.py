import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app as app_module
from run_code import RunnerUnavailableError


class RunRouteTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def test_run_requires_login(self):
        response = self.client.post("/run", json={
            "language": "python", "code": "print(1)", "input": ""
        })
        self.assertEqual(response.status_code, 401)

    def test_invalid_and_oversized_requests_are_rejected(self):
        with self.client.session_transaction() as session:
            session["username"] = "tester"
        invalid = self.client.post("/run", data="not json", content_type="text/plain")
        self.assertEqual(invalid.status_code, 400)
        oversized = self.client.post("/run", json={
            "language": "python", "code": "x" * (101 * 1024), "input": ""
        })
        self.assertEqual(oversized.status_code, 413)
        self.assertIn("too large", oversized.json["output"])

    @patch.object(app_module, "save_code")
    @patch.object(app_module, "log_user_activity")
    @patch.object(app_module, "execute_code")
    def test_runner_failure_does_not_save_code(self, execute, log, save):
        with self.client.session_transaction() as session:
            session["username"] = "tester"
        execute.side_effect = RunnerUnavailableError("Docker unavailable")

        response = self.client.post("/run", json={
            "language": "python", "code": "print(1)", "input": ""
        })

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["output"], "Docker unavailable")
        log.assert_not_called()
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
