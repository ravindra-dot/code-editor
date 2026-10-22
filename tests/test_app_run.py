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

    @patch.object(app_module, "save_code")
    @patch.object(app_module, "execute_code", return_value="1")
    def test_run_is_public_and_does_not_save(self, execute, save):
        response = self.client.post("/run", json={
            "language": "python", "code": "print(1)", "input": ""
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["output"], "1")
        execute.assert_called_once()
        save.assert_not_called()

    @patch.object(app_module, "save_code")
    @patch.object(app_module, "log_user_activity")
    def test_save_requires_login_and_valid_source(self, log, save):
        payload = {"language": "python", "code": "print(1)"}
        self.assertEqual(self.client.post("/save", json=payload).status_code, 401)
        with self.client.session_transaction() as session:
            session["username"] = "tester"
        self.assertEqual(self.client.post("/save", json={"language": "javascript", "code": "x"}).status_code, 400)
        self.assertEqual(self.client.post("/save", json=payload).status_code, 201)
        save.assert_called_once_with("tester", "print(1)", "python")
        log.assert_called_once()

    def test_editors_are_public(self):
        self.assertEqual(self.client.get("/editor").status_code, 200)
        self.assertEqual(self.client.get("/html-editor").status_code, 200)

    def test_terminal_is_scoped_to_browser_session(self):
        class FakeTerminal:
            id = "test-terminal"
            language = "python"
            code = "print(1)"

            def snapshot(self, offset):
                return {"output": "1", "offset": 1, "done": True}

            def stop(self):
                pass

        owners = {}
        terminal = FakeTerminal()

        def create(owner, language, code):
            owners[owner] = terminal
            return terminal

        def get(session_id, owner):
            return owners.get(owner) if session_id == terminal.id else None

        with patch.object(app_module, "create_session", side_effect=create), \
                patch.object(app_module, "get_session", side_effect=get):
            response = self.client.post("/terminal", json={"language": "python", "code": "print(1)"})
            self.assertEqual(response.status_code, 201)
            self.assertEqual(self.client.get("/terminal/test-terminal").status_code, 200)
            other = app_module.app.test_client()
            self.assertEqual(other.get("/terminal/test-terminal").status_code, 404)
            self.assertEqual(other.post("/terminal/test-terminal/stop").status_code, 404)

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
