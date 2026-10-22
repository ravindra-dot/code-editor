# CodeSphere

A Flask based browser editor for Python, C, and C++, plus an HTML/CSS/JavaScript preview editor. Submitted Python, C, and C++ code runs in a short-lived Linux Docker container. It does not execute with the Flask server's Python interpreter or host compilers.

## Local setup on Windows

1. Start Docker Desktop and select **Linux containers**. Check that `docker info` succeeds.
2. From the repository root, build the code runner image:

   ```powershell
   docker build --pull -t codesphere-runner:latest ./runner
   ```

3. Install the Flask dependencies in a Python environment:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Start the web app from the repository root:

   ```powershell
   python backend/app.py
   ```

   Visit `http://127.0.0.1:5500`.

Accounts, activity, and saved code are stored in `data/codesphere.sqlite3`. The app creates its tables automatically. The `data/` directory is ignored by Git. Set `CODESPHERE_DB_PATH` to an absolute path to use a different local file. For a stable login session across restarts, the app stores a local secret in the same ignored directory; in a hosted environment set `CODESPHERE_SECRET_KEY` to a long random value.

Anyone can open either editor and run code. The main editor's **Save code** button requires login; running code does not automatically add it to saved history. Monaco provides syntax highlighting, bracket and quote completion, word suggestions, and Python/C/C++ snippets. **Light editor** toggles the editor and terminal theme and remembers the choice in this browser.

The Flask app runs on Windows, while Docker Desktop runs submitted code inside a Linux VM and container. The runner image includes Python, GCC, and G++; the host does not need GCC or G++. Rebuild the image after editing either runner script or `runner/Dockerfile`.

The Dockerfile defaults to `python:3.12-bookworm`. For an offline local check, you can override `RUNNER_BASE` with an already cached compatible full Python image. Rebuild with `--pull` and without that override when network access is available so the image receives current base updates.

The runner image also includes Python NumPy, pandas, Matplotlib, Pillow, and SymPy, plus C++ Eigen and nlohmann/json headers. The C and C++ standard libraries are included with GCC/G++. These packages are available to submitted programs without installation. Network access remains disabled, so packages that call external APIs are not useful in the runner. Plots and image files written by programs are not displayed or downloadable yet; text output is supported.

Run the host-side tests with `python -B -m unittest discover -s tests -v`. After building the image, verify all three languages with `python -B tests/docker_smoke.py` and their interactive prompts with `python -B tests/interactive_smoke.py`.

With Docker running, `python -B tests/live_integration.py` checks signup, login, execution, profile, project, and saved history using a disposable SQLite database.

## Vercel hosting

This repository is **not ready to host the full code editor on Vercel alone**. Vercel supports Flask functions, but [function filesystems are read-only apart from temporary scratch space](https://vercel.com/docs/functions/runtimes). A SQLite file in the function will not keep accounts or history across instances and redeployments. The interactive runner also starts separate restricted containers with `docker run`; packaging the Flask app as a [Vercel container function](https://vercel.com/kb/guide/does-vercel-support-docker-deployments) does not provide the Docker daemon or persistent process state that this runner needs. An external durable database and an external code-execution service are needed before deploying the full app there. Keep the local SQLite file and secret out of the deployment bundle.

For a small public deployment on one Linux VPS, follow [the deployment guide](deploy/README.md). It uses Gunicorn behind Caddy with HTTPS, a persistent SQLite directory, the restricted Docker runner, and basic request limits. You will need to provide the VPS and domain; this repository cannot publish itself to the internet.

## Execution limits

The main editor has a terminal panel. Press **Run Code**, click the terminal, and type when the program prompts. Press **Stop** to end a running program. A separate prefilled input box is no longer needed. The terminal runs the submitted program; it is not a general shell.

Each run starts a new container. Source and terminal keystrokes arrive over stdin, and the container has no mounted host directories, no network, a read-only image filesystem, temporary scratch space, a non-root user, dropped capabilities, and limits for memory, CPU, and process count. Compilation has a 10 second limit. The interactive program has a 90 second limit and a 105 second host deadline. Source is limited to 64 KiB, each input message to 16 KiB, and output to 64 KiB. The older `/run` endpoint remains available with its 5 second program and 30 second outer limits.
Each runner container has a 512 MiB memory limit.

The Flask development debugger is disabled, and the old route that served host-side `uploads/` files has been removed. Old files in `uploads/` are not used by the Docker runner.

Docker isolation reduces exposure to the host but is not a guarantee against every container escape or denial of service. Keep Docker Desktop and the runner image updated. Do not expose this development app to untrusted public users without additional controls such as request rate limits, concurrency limits, and stronger isolation.

If running code returns **503**, check that Docker Desktop is running in Linux container mode and that the runner image was built. The browser preview editor runs HTML/CSS/JavaScript in an iframe; it does not use this Docker runner.
