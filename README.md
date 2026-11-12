# CodeSphere

[![Tests](https://github.com/ravindra-dot/code-editor/actions/workflows/tests.yml/badge.svg)](https://github.com/ravindra-dot/code-editor/actions/workflows/tests.yml)

**A browser-based code editor for Python, C, and C++, with interactive program input and a separate HTML/CSS/JavaScript preview.**

CodeSphere is a small Flask application for writing and trying code without installing language compilers on the client device. Monaco powers the Python/C/C++ editor, xterm.js shows program output and accepts input, and each run executes in a short-lived Docker container on the server.

> CodeSphere runs individual programs. It does not provide a persistent shell, multi-file workspaces, debugging, or VS Code extension support.

## Features

| Feature | What it does |
| --- | --- |
| Python, C, and C++ editor | Syntax highlighting, suggestions, snippets, language selection, local drafts, and a theme toggle. |
| Interactive runs | Stream output, type input into a running program, and stop it from the browser. |
| Web preview | Edit HTML, CSS, and JavaScript in a separate page with a sandboxed iframe preview. |
| Accounts and history | Save code and revisit recent activity with local SQLite storage. |
| Restricted execution | Run each submitted program in a fresh Linux container with resource and time limits. |

The runner image includes Python, GCC, G++, NumPy, pandas, Matplotlib, Pillow, SymPy, Eigen, and nlohmann/json. Programs cannot install packages or use the network. Generated images and other files are not returned to the browser; the execution API returns text output.

## Quick start

**Requirements:** Python, Docker Desktop or Docker Engine, and a browser. On Windows, Docker Desktop must use Linux containers. The host does not need GCC or G++.

From the repository root:

```powershell
docker build --pull -t codesphere-runner:latest ./runner
python -m pip install -r requirements.txt
python backend/app.py
```

Open <http://127.0.0.1:5500>. Docker must be running when you execute Python, C, or C++ programs. The HTML/CSS/JavaScript preview works without Docker. Frontend assets load from CDNs, so the browser needs an internet connection for the editor libraries and styling.

The app creates `data/codesphere.sqlite3` and a local Flask secret under the ignored `data/` directory. Set `CODESPHERE_DB_PATH` to use another local database path. Do not commit either file.

## Use the editors

1. Visit `/editor`, choose Python, C, or C++, write a program, and select **Run Code**. Type in the terminal panel when your program requests input. The panel connects to the running program; it is not a general-purpose shell.
2. Visit `/html-editor` for the HTML/CSS/JavaScript preview. Its iframe uses `sandbox="allow-scripts"`.
3. Create an account to save Python/C/C++ snippets and view recent activity. You can edit and run code without signing in. Runs are not saved automatically.

If execution returns **503**, start Docker Desktop and build the `codesphere-runner:latest` image with the command above.

## How it works

```text
Browser (Monaco + xterm.js)
          │
          ▼
Flask routes ─────────── SQLite (accounts, saved snippets, activity)
          │
          ▼
Short-lived Docker runner (Python / GCC / G++)
```

- [`backend/app.py`](backend/app.py) provides authentication, save, execution, and terminal routes.
- [`backend/database.py`](backend/database.py) stores accounts, recent activity, and saved snippets in SQLite.
- [`backend/run_code.py`](backend/run_code.py) and [`backend/interactive.py`](backend/interactive.py) start and manage restricted containers.
- [`frontend/`](frontend/) contains the Jinja pages and browser scripts.
- [`runner/`](runner/) contains the Docker image and in-container execution code.

The runner uses a read-only image filesystem, a non-root user, no network or host mounts, dropped capabilities, temporary working directories, and limits on CPU, memory, processes, output, and time. These controls reduce risk, but running other people's code still requires a carefully maintained host.

## Tests

Run the host-side suite:

```powershell
python -B -m unittest discover -s tests -v
```

With the runner image built and Docker running, exercise Python, C, C++, and interactive input:

```powershell
python -B tests/docker_smoke.py
python -B tests/interactive_smoke.py
```

`python -B tests/live_integration.py` checks signup, login, execution, profile, projects, and saved history using a disposable SQLite database.

## Sharing and deployment

The `python backend/app.py` command starts Flask's development server for local testing. For shared access, use a production WSGI server, a stable `CODESPHERE_SECRET_KEY`, and the public-mode settings described in the [single-host deployment guide](deploy/README.md). Keep the Docker socket private and verify the reverse proxy or tunnel preserves the client address used by rate limits. Interactive sessions live in one server process, so the current deployment uses one worker.

GitHub Pages can show this README as documentation, but it cannot run the Flask app or Docker runner. A local SQLite database is not durable in Vercel Functions, and the runner requires a Docker-capable host. The full application therefore cannot run on GitHub Pages or Vercel alone.

## Contributing

Bug reports and focused improvements are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Please report security issues using the instructions in [SECURITY.md](SECURITY.md).

## License

CodeSphere is available under the [MIT License](LICENSE).
