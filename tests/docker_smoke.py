"""Trusted end-to-end runner checks. Requires a built Docker image."""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import run_code
import app as app_module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=run_code.RUNNER_IMAGE)
    args = parser.parse_args()
    run_code.RUNNER_IMAGE = args.image

    cases = [
        ("python", "print(input().upper())", "hello\n", "HELLO"),
        ("python", "print('✓')", "", "✓"),
        ("c", '#include <stdio.h>\nint main(void) { puts("Hello C"); }', "", "Hello C"),
        ("cpp", '#include <iostream>\nint main() { std::cout << "Hello C++\\n"; }', "", "Hello C++"),
    ]
    for language, code, input_text, expected in cases:
        actual = run_code.execute_code(language, code, input_text)
        if actual != expected:
            raise AssertionError(f"{language}: expected {expected!r}, got {actual!r}")
        print(f"{language}: OK")

    timeout_output = run_code.execute_code("python", "while True: pass", "")
    if timeout_output != "Time limit exceeded":
        raise AssertionError(f"timeout: got {timeout_output!r}")
    print("timeout: OK")

    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    with client.session_transaction() as session:
        session["username"] = "smoke-test"
    with patch.object(app_module, "log_user_activity"), patch.object(app_module, "save_code"):
        response = client.post("/run", json={
            "language": "python", "code": "print(2 + 3)", "input": ""
        })
    if response.status_code != 200 or response.json["output"] != "5":
        raise AssertionError(f"Flask /run: {response.status_code}, {response.json!r}")
    print("Flask /run: OK")


if __name__ == "__main__":
    main()
