import os
import secrets
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from run_code import execute_code, validate_source, RunnerTimeoutError, RunnerUnavailableError
from interactive import create_session, get_session
from limits import allow
from database import (
    create_user, get_user, verify_password, log_user_activity,
    get_recent_activities, save_code, get_recent_codes, get_saved_code
)

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
PUBLIC_MODE = os.environ.get("CODESPHERE_PUBLIC") == "1"
if PUBLIC_MODE:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
sync_run_slots = threading.BoundedSemaphore(4)


def secret_key():
    configured = os.environ.get("CODESPHERE_SECRET_KEY")
    if configured:
        if PUBLIC_MODE and len(configured) < 32:
            raise RuntimeError("CODESPHERE_SECRET_KEY must be at least 32 characters in public mode")
        return configured
    if PUBLIC_MODE or os.environ.get("VERCEL"):
        raise RuntimeError("Set CODESPHERE_SECRET_KEY for a stable login session")
    path = Path(__file__).resolve().parents[1] / "data" / "flask-secret"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(secrets.token_hex(32), encoding="ascii")
    return path.read_text(encoding="ascii").strip()


app.secret_key = secret_key()
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = PUBLIC_MODE or bool(os.environ.get("VERCEL"))


@app.before_request
def public_rate_limit():
    if not PUBLIC_MODE or request.method != "POST":
        return None
    origin = request.headers.get("Origin")
    if origin and origin.rstrip("/") != request.host_url.rstrip("/"):
        return jsonify({"message": "Invalid request origin"}), 403
    category = {
        "/run": ("execution", 10),
        "/terminal": ("execution", 10),
        "/auth/login": ("auth", 8),
        "/auth/signup": ("auth", 8),
    }.get(request.path)
    if category and not allow(request.remote_addr or "unknown", *category):
        return jsonify({"message": "Too many requests; try again in a minute"}), 429
    return None


@app.errorhandler(413)
def request_too_large(error):
    if request.path == "/run":
        return jsonify({"output": "Request is too large (100 KiB maximum)"}), 413
    if request.path.startswith("/terminal"):
        return jsonify({"message": "Request is too large (100 KiB maximum)"}), 413
    return error

@app.route('/')
def home():
    return render_template('Home.html', username=session.get("username"))


@app.route('/editor')
def index():
    selected = None
    if request.args.get("code_id") and "username" in session:
        try:
            selected = get_saved_code(session["username"], int(request.args["code_id"]))
        except ValueError:
            pass
    return render_template('index.html', selected_code=selected)


@app.route('/html-editor')
def html_editor():
    return render_template('web-editor/weditor.html')

@app.route('/signup')
def signup_page():
    return render_template('auth.html')


@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Expected a JSON object"}), 400

    full_name = data.get("fullName")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not all(isinstance(value, str) and value.strip() for value in (full_name, username, email, password)):
        return jsonify({"message": "All fields are required!"}), 400
    full_name, username, email = full_name.strip(), username.strip(), email.strip()
    if len(full_name) > 100 or len(username) > 50 or len(email) > 100 or len(password) < 8:
        return jsonify({"message": "Check field lengths; password must have at least 8 characters"}), 400

    result, status = create_user(full_name, username, email, password)

    if status == 201:
        session["username"] = username
        session["full_name"] = full_name
        log_user_activity(username, "Signed Up")

    return jsonify(result), status


@app.route('/login')
def login_page():
    return render_template('auth.html')


@app.route('/auth/login', methods=['POST'])
def authenticate():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return render_template("auth.html", error="Both username and password are required!")

    user = get_user(username)

    if not user:
        return render_template("auth.html", error="No user found with this username!")

    if not verify_password(user["password"], password):
        return render_template("auth.html", error="Invalid password!")

    session["username"] = username
    session["full_name"] = user["full_name"]
    log_user_activity(username, "Logged In")

    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if "username" not in session:
        return redirect(url_for("login_page"))

    username = session["username"]
    activities = get_recent_activities(username)
    codes = get_recent_codes(username)

    return render_template(
        "profile.html",
        full_name=session["full_name"],
        username=username,
        activities=activities,
        codes=codes
    )


@app.route('/project')
def project():
    if "username" not in session:
        return redirect(url_for("login_page"))

    username = session["username"]
    codes = get_recent_codes(username)

    return render_template(
        "project.html",
        full_name=session["full_name"],
        username=username,
        codes=codes
    )


@app.route('/logout')
def logout():
    if "username" in session:
        log_user_activity(session["username"], "Logged Out")
    session.clear()
    return redirect(url_for("home"))


@app.route('/run', methods=['POST'])
def run_code():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"output": "Expected a JSON object"}), 400
    language = data.get("language")
    code = data.get("code")
    user_input = data.get("input", "")

    try:
        if not sync_run_slots.acquire(blocking=False):
            return jsonify({"output": "Server is busy; try again shortly"}), 429
        try:
            output = execute_code(language, code, user_input)
        finally:
            sync_run_slots.release()

        return jsonify({"output": output})
    except ValueError as e:
        return jsonify({"output": str(e)}), 400
    except RunnerUnavailableError as e:
        return jsonify({"output": str(e)}), 503
    except RunnerTimeoutError as e:
        return jsonify({"output": str(e)}), 504
    except Exception:
        app.logger.exception("Code execution request failed")
        return jsonify({"output": "An internal error occurred"}), 500


@app.route('/terminal', methods=['POST'])
def start_terminal():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Expected a JSON object"}), 400
    try:
        validate_source(data.get("language"), data.get("code"))
        owner = session.get("execution_id")
        if owner is None:
            owner = secrets.token_urlsafe(32)
            session["execution_id"] = owner
        terminal = create_session(owner, data.get("language"), data.get("code"))
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    except FileNotFoundError:
        return jsonify({"message": "Docker CLI was not found on PATH"}), 503
    return jsonify({"id": terminal.id}), 201


@app.route('/save', methods=['POST'])
def save_current_code():
    if "username" not in session:
        return jsonify({"message": "Log in to save code"}), 401
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Expected a JSON object"}), 400
    language, code = data.get("language"), data.get("code")
    try:
        validate_source(language, code)
    except ValueError as error:
        return jsonify({"message": str(error)}), 400
    save_code(session["username"], code, language)
    log_user_activity(session["username"], f"Saved {language} code")
    return jsonify({"message": "Code saved"}), 201


@app.route('/terminal/<session_id>', methods=['GET'])
def poll_terminal(session_id):
    terminal = get_session(session_id, session.get("execution_id"))
    if terminal is None:
        return jsonify({"message": "Terminal not found"}), 404
    try:
        offset = int(request.args.get("offset", "0"))
        return jsonify(terminal.snapshot(offset))
    except ValueError as error:
        return jsonify({"message": str(error)}), 400


@app.route('/terminal/<session_id>/input', methods=['POST'])
def terminal_input(session_id):
    terminal = get_session(session_id, session.get("execution_id"))
    if terminal is None:
        return jsonify({"message": "Terminal not found"}), 404
    data = request.get_json(silent=True)
    try:
        terminal.send(data.get("input") if isinstance(data, dict) else None)
        return jsonify({"ok": True})
    except ValueError as error:
        return jsonify({"message": str(error)}), 400


@app.route('/terminal/<session_id>/stop', methods=['POST'])
def stop_terminal(session_id):
    terminal = get_session(session_id, session.get("execution_id"))
    if terminal is None:
        return jsonify({"message": "Terminal not found"}), 404
    terminal.stop()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=False, port=5500)
