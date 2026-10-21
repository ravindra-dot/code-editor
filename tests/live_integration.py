"""Exercise real Docker execution with a disposable SQLite account."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app as app_module
import database


def expect(response, status, label):
    if response.status_code != status:
        raise AssertionError(f"{label}: expected HTTP {status}, got {response.status_code}: {response.get_json(silent=True)}")
    print(f"{label}: OK")


def main():
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=data_dir) as directory:
        previous = os.environ.get("CODESPHERE_DB_PATH")
        os.environ["CODESPHERE_DB_PATH"] = str(Path(directory) / "integration.sqlite3")
        try:
            app_module.app.config["TESTING"] = True
            client = app_module.app.test_client()
            expect(client.get("/"), 200, "Home page")
            expect(client.post("/auth/signup", json={
                "fullName": "Integration Test", "username": "integration_test",
                "email": "integration@example.invalid", "password": "test-password-123",
            }), 201, "Sign up")
            expect(client.get("/editor"), 200, "Editor page")
            expect(client.get("/html-editor"), 200, "HTML editor")
            expect(client.get("/logout"), 302, "Log out")
            expect(client.post("/auth/login", data={
                "username": "integration_test", "password": "test-password-123",
            }), 302, "Log in")

            examples = [
                ("python", "print(2 + 3)", "5"),
                ("c", '#include <stdio.h>\nint main(void) { puts("Hello C"); }', "Hello C"),
                ("cpp", '#include <iostream>\nint main() { std::cout << "Hello C++\\n"; }', "Hello C++"),
            ]
            for language, code, expected in examples:
                response = client.post("/run", json={
                    "language": language, "code": code, "input": "",
                })
                expect(response, 200, f"Run {language}")
                if response.json.get("output") != expected:
                    raise AssertionError(f"Run {language}: unexpected output")

            expect(client.get("/profile"), 200, "Profile page")
            expect(client.get("/project"), 200, "Project page")
            languages = {row["language"] for row in database.get_recent_codes("integration_test")}
            if languages != {"python", "c", "cpp"}:
                raise AssertionError(f"Saved history: unexpected languages {languages}")
            print("Saved SQLite code history: OK")
        finally:
            if previous is None:
                os.environ.pop("CODESPHERE_DB_PATH", None)
            else:
                os.environ["CODESPHERE_DB_PATH"] = previous
    print("Disposable SQLite database removed")


if __name__ == "__main__":
    main()
