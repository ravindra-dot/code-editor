"""Exercise live terminal input and output through Flask and Docker."""

import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import app as app_module


def run_case(client, language, code, prompt, expected):
    response = client.post("/terminal", json={"language": language, "code": code})
    assert response.status_code == 201, response.json
    session_id = response.json["id"]
    output = ""
    offset = 0
    deadline = time.monotonic() + 25
    while prompt not in output and time.monotonic() < deadline:
        response = client.get(f"/terminal/{session_id}?offset={offset}")
        assert response.status_code == 200, response.json
        output += response.json["output"]
        offset = response.json["offset"]
        assert not response.json["done"], output
        time.sleep(0.1)
    assert prompt in output, output
    response = client.post(f"/terminal/{session_id}/input", json={"input": "Ada\r"})
    assert response.status_code == 200, response.json
    while time.monotonic() < deadline:
        response = client.get(f"/terminal/{session_id}?offset={offset}")
        assert response.status_code == 200, response.json
        output += response.json["output"]
        offset = response.json["offset"]
        if response.json["done"]:
            break
        time.sleep(0.1)
    assert response.json["done"] and expected in output, output
    print(f"{language} interactive terminal: OK")


def main():
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    editor_page = client.get("/editor")
    assert editor_page.status_code == 200
    assert b'id="terminal"' in editor_page.data
    assert b'id="input-box"' not in editor_page.data
    with patch.object(app_module, "log_user_activity"), patch.object(app_module, "save_code"):
        run_case(client, "python", 'name = input("Name? ")\nprint("Hello", name)', "Name? ", "Hello Ada")
        run_case(client, "c", '#include <stdio.h>\nint main(void) { char name[40]; printf("Name? "); scanf("%39s", name); printf("Hello %s\\n", name); }', "Name? ", "Hello Ada")
        run_case(client, "cpp", '#include <iostream>\n#include <string>\nint main() { std::string name; std::cout << "Name? "; std::cin >> name; std::cout << "Hello " << name << "\\n"; }', "Name? ", "Hello Ada")
        response = client.post("/terminal", json={"language": "python", "code": "import time\nwhile True: time.sleep(1)"})
        assert response.status_code == 201, response.json
        session_id = response.json["id"]
        other = app_module.app.test_client()
        assert other.get(f"/terminal/{session_id}").status_code == 404
        assert other.post(f"/terminal/{session_id}/input", json={"input": "x"}).status_code == 404
        assert other.post(f"/terminal/{session_id}/stop").status_code == 404
        assert client.post(f"/terminal/{session_id}/stop").status_code == 200
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if client.get(f"/terminal/{session_id}").json["done"]:
                break
            time.sleep(0.1)
        assert client.get(f"/terminal/{session_id}").json["done"]
        print("Terminal ownership and Stop: OK")
    print("Anonymous terminal access and ownership: OK")


if __name__ == "__main__":
    main()
