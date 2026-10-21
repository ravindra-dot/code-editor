import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app as app_module
import database


class SQLiteTests(unittest.TestCase):
    def setUp(self):
        data_dir = Path(__file__).resolve().parents[1] / "data"
        data_dir.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=data_dir)
        self.db_path = str(Path(self.temp.name) / "codesphere.sqlite3")
        self.env = patch.dict(os.environ, {"CODESPHERE_DB_PATH": self.db_path})
        self.env.start()
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_signup_login_and_saved_code_survive_new_connections(self):
        signup = self.client.post("/auth/signup", json={
            "fullName": "Test User", "username": "tester",
            "email": "tester@example.invalid", "password": "long-test-password",
        })
        self.assertEqual(signup.status_code, 201)
        self.assertTrue(database.verify_password(database.get_user("tester")["password"], "long-test-password"))
        database.save_code("tester", "print(42)", "python")
        code = database.get_recent_codes("tester")[0]
        self.assertEqual(database.get_saved_code("tester", code["id"])["code"], "print(42)")
        self.assertIsNone(database.get_saved_code("someone_else", code["id"]))
        editor = self.client.get(f'/editor?code_id={code["id"]}')
        self.assertEqual(editor.status_code, 200)
        self.assertIn(b'print(42)', editor.data)
        self.assertEqual(self.client.get("/html-editor").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.client.get("/logout")
        self.assertEqual(self.client.post("/auth/login", data={
            "username": "tester", "password": "long-test-password"
        }).status_code, 302)

    def test_code_history_keeps_ten_latest_entries(self):
        result, status = database.create_user("Test", "tester", "test@example.invalid", "password123")
        self.assertEqual(status, 201, result)
        for index in range(12):
            database.save_code("tester", f"print({index})", "python")
        codes = database.get_recent_codes("tester")
        self.assertEqual(len(codes), 10)
        self.assertEqual(codes[0]["code"], "print(11)")
        self.assertEqual(codes[-1]["code"], "print(2)")


if __name__ == "__main__":
    unittest.main()
