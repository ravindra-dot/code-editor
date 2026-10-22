# Deploy CodeSphere on one Linux VPS

This is a single-host deployment recipe. It requires a Linux VPS with Docker Engine, Python 3.12, Caddy, a domain pointed at the VPS, and enough memory for the web process plus up to eight 512 MiB runners. Use a dedicated host for untrusted code. Do not use Vercel for this configuration.

1. Create a dedicated `codesphere` system user. Install Docker Engine, Caddy, Python 3.12, and the Python venv package using your distribution's supported packages. Add the user to the `docker` group. **Docker group membership grants broad host control**; do not share this host with sensitive workloads. Keep the Docker daemon and OS patched.
2. Put this repository at `/opt/codesphere`, owned by `codesphere`. Create `/var/lib/codesphere`, owned by that user, for persistent SQLite data. Back up this directory regularly.
3. Build the runner image on the VPS: `docker build --pull -t codesphere-runner:latest ./runner`. The runner installs a fixed set of libraries during this build. Submitted programs cannot install packages or access the network.
4. Create a virtual environment at `/opt/codesphere/.venv` and install `requirements-prod.txt`. Do this as the `codesphere` user.
5. Create `/etc/codesphere.env`, readable by root and `codesphere` only, with:

   ```ini
   CODESPHERE_PUBLIC=1
   CODESPHERE_SECRET_KEY=<a unique random value of at least 32 bytes>
   CODESPHERE_DB_PATH=/var/lib/codesphere/codesphere.sqlite3
   ```

   Generate the secret on the server with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. Never commit the environment file or database.
6. Copy `deploy/codesphere.service.example` to `/etc/systemd/system/codesphere.service`, adjust paths if needed, then run `systemctl daemon-reload && systemctl enable --now codesphere`. The single Gunicorn worker is intentional: terminal sessions and request limits are held in process memory. Multiple workers or multiple servers need shared session and limit storage first.
7. Replace `compiler.example.com` in `deploy/Caddyfile.example` with your domain and add it to Caddy's configuration. Start Caddy and allow inbound ports 80 and 443. Keep Gunicorn bound to `127.0.0.1`; do not expose port 8000 or the Docker socket publicly. Caddy terminates HTTPS and forwards the client address used by request limits.
8. Verify `/`, `/editor`, and `/html-editor` over HTTPS. Run one small Python, C, and C++ program, then check terminal input, signup, login, and save. `journalctl -u codesphere -e` shows web process errors.

The public service limits program starts to ten per client IP per minute, login and signup attempts to eight per minute, synchronous runs to four at a time, and interactive sessions to eight globally and two per browser. These controls are for a small deployment; they are not a substitute for stronger isolation, monitoring, and distributed abuse protection at larger scale. Avoid running the app on a machine with private data or other services.

The browser preview executes HTML/CSS/JavaScript in a sandboxed iframe. Python, C, and C++ run in the Docker image with no network, a read-only filesystem, temporary working directories, and resource and time limits. Libraries must be added to the image by an administrator and rebuilt; user code cannot run `pip install` or `apt install`.
