"""Local SQLite storage for accounts, activity, and saved code."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "codesphere.sqlite3"
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_activities (
    id INTEGER PRIMARY KEY,
    username TEXT,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS codes (
    id INTEGER PRIMARY KEY,
    username TEXT,
    code TEXT NOT NULL,
    language TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activities_user_time ON user_activities(username, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_codes_user_time ON codes(username, timestamp DESC);
"""


def database_path():
    return Path(os.environ.get("CODESPHERE_DB_PATH", DEFAULT_DATABASE_PATH)).expanduser().resolve()


def get_db_connection():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.executescript(SCHEMA)
    return connection


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_user(full_name, username, email, password):
    """Create an account, storing only a password hash."""
    with closing(get_db_connection()) as connection:
        if connection.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            return {"message": "Username already taken!"}, 400
        if connection.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            return {"message": "Email already registered!"}, 400
        try:
            with connection:
                connection.execute(
                    "INSERT INTO users (full_name, username, email, password) VALUES (?, ?, ?, ?)",
                    (full_name, username, email, generate_password_hash(password)),
                )
                connection.execute(
                    "INSERT INTO user_activities (username, action, timestamp) VALUES (?, ?, ?)",
                    (username, "Account Created", _now()),
                )
        except sqlite3.IntegrityError:
            return {"message": "Username or email already registered!"}, 400
    return {"message": "Signup successful!"}, 201


def get_user(username):
    with closing(get_db_connection()) as connection:
        row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)


def log_user_activity(username, action):
    with closing(get_db_connection()) as connection:
        with connection:
            connection.execute(
                "INSERT INTO user_activities (username, action, timestamp) VALUES (?, ?, ?)",
                (username, action, _now()),
            )
            connection.execute(
                "DELETE FROM user_activities WHERE username = ? AND id NOT IN "
                "(SELECT id FROM user_activities WHERE username = ? ORDER BY timestamp DESC, id DESC LIMIT 10)",
                (username, username),
            )


def get_recent_activities(username, limit=5):
    with closing(get_db_connection()) as connection:
        rows = connection.execute(
            "SELECT * FROM user_activities WHERE username = ? ORDER BY timestamp DESC, id DESC LIMIT ?",
            (username, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def save_code(username, code, language):
    with closing(get_db_connection()) as connection:
        with connection:
            connection.execute(
                "INSERT INTO codes (username, code, language, timestamp) VALUES (?, ?, ?, ?)",
                (username, code, language, _now()),
            )
            connection.execute(
                "DELETE FROM codes WHERE username = ? AND id NOT IN "
                "(SELECT id FROM codes WHERE username = ? ORDER BY timestamp DESC, id DESC LIMIT 10)",
                (username, username),
            )


def get_recent_codes(username, limit=10):
    with closing(get_db_connection()) as connection:
        rows = connection.execute(
            "SELECT * FROM codes WHERE username = ? ORDER BY timestamp DESC, id DESC LIMIT ?",
            (username, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def get_saved_code(username, code_id):
    with closing(get_db_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM codes WHERE username = ? AND id = ?", (username, code_id)
        ).fetchone()
        return dict(row) if row else None
