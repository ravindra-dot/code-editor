# CodeSphere

### Write code in your browser. Run it in a container.

CodeSphere is a small Flask web app with two editors: an interactive **Python, C, and C++ editor** and a separate **HTML, CSS, and JavaScript preview editor**. It also supports accounts, saved code, and recent activity.

> **Viewing this on GitHub Pages?** This page is the project guide. GitHub Pages can publish this documentation, but it cannot run the Flask server, SQLite database, or Docker code runner. [Run CodeSphere locally](#run-locally) or use a server that supports those components.

[Features](#features) · [Run locally](#run-locally) · [Using the editors](#using-the-editors) · [GitHub Pages](#github-pages) · [Tests](#tests) · [Deployment](#deployment)

## Features

| | What you can do |
| --- | --- |
| **Python, C, and C++** | Edit with Monaco, run programs, and interact with input and output in a terminal panel. |
| **Web preview** | Edit HTML, CSS, and JavaScript and see the result in a sandboxed iframe. |
| **Accounts and projects** | Sign up, save code, and revisit saved work and recent activity. |
| **Container runner** | Compile or execute submitted programs in short-lived Linux Docker containers with resource limits. |

The main editor includes syntax highlighting, suggestions, snippets, and a light theme toggle. The runner image includes Python, GCC, G++, NumPy, pandas, Matplotlib, Pillow, SymPy, Eigen, and nlohmann/json. Submitted programs cannot access the network or install more packages. Program-created plots and image files are not displayed or downloadable; text output is supported.

## Run locally

### Before you start

- Install Python and Docker Desktop. On Windows, select **Linux containers** in Docker Desktop.
- Run the commands below from the repository root.
- Confirm Docker is available with `docker info`.

### 1. Build the runner

```powershell
docker build --pull -t codesphere-runner:latest ./runner
```

This image contains the language runtimes and compilers; you do not need GCC or G++ on the host. Rebuild it after changing `runner/Dockerfile` or the runner scripts.

### 2. Install the web app dependencies

```powershell
python -m pip install -r requirements.txt
```

Using a virtual environment is recommended. The local `env/`, `venv/`, and `.venv/` folders are ignored by Git.

### 3. Start CodeSphere

```powershell
python backend/app.py
```

Open **<http://127.0.0.1:5500>** in your browser.

The app creates its local SQLite database in `data/codesphere.sqlite3`. To use another local file, set `CODESPHERE_DB_PATH` to its absolute path. The database and local session secret are ignored by Git. For a hosted installation, set `CODESPHERE_SECRET_KEY` to a long random value.

## Using the editors

1. Open **`/editor`** for Python, C, or C++. Choose a language, enter code, and press **Run Code**.
2. Click the terminal and type when your program requests input. Press **Stop** to end a running program. This terminal runs your program; it is not a general shell.
3. Open **`/html-editor`** to preview HTML, CSS, and JavaScript in the browser.
4. Create an account and sign in to use **Save code**, projects, and recent activity. You can open either editor and run code without signing in. Running code does not save it automatically.

If a run returns **503**, check that Docker Desktop is running in Linux container mode and that `codesphere-runner:latest` was built. The HTML/CSS/JavaScript preview does not need Docker.

## GitHub Pages

GitHub Pages can publish this README as a static project page. To use it, push the repository to GitHub, then open **Settings → Pages → Build and deployment** and select **Deploy from a branch**, **`main`**, and **`/(root)`**. This repository has no root `index.html` or `index.md`, so Pages can use this root `README.md` as its entry file. See [GitHub's publishing source guide](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) and [entry file guide](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

The Pages site is documentation for CodeSphere. The `/editor` and `/html-editor` routes described above belong to the running Flask app; they are not available on GitHub Pages. Hosting the working app requires a Python server, persistent storage, and a Docker-capable runner host.

## Tests

Run the host-side tests from the repository root:

```powershell
python -B -m unittest discover -s tests -v
```

After building the runner image, check all three languages and interactive input:

```powershell
python -B tests/docker_smoke.py
python -B tests/interactive_smoke.py
```

With Docker running, `python -B tests/live_integration.py` checks signup, login, execution, profile, projects, and saved history with a disposable SQLite database.

## Deployment

For a small public deployment on one Linux VPS, follow the [deployment guide](https://github.com/raveendras-git/code-editor/blob/main/deploy/README.md). It covers Gunicorn, Caddy with HTTPS, persistent SQLite storage, the Docker runner, and basic request limits. A VPS and domain are required.

**The full app cannot run on GitHub Pages or Vercel alone.** Pages hosts static content. A local SQLite file in a Vercel Function is not durable across instances and deployments, and this runner needs a separate Docker-capable host. A different hosting design would need durable external storage and an external code-execution service.

Each submitted Python, C, or C++ run uses a new container with no network or host mounts, a read-only image filesystem, a non-root user, dropped capabilities, temporary scratch space, and CPU, memory, process, output, and time limits. Containers have a 512 MiB memory limit. Docker isolation reduces risk but does not guarantee protection from every container escape or denial of service. Keep the host and runner image updated before offering public access.

---

**Project layout:** `backend/` contains Flask routes and SQLite access; `frontend/` contains Jinja templates and browser scripts; `runner/` contains the Docker execution image; `tests/` contains automated and smoke tests.
