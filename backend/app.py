from flask import Flask, render_template, request, jsonify, redirect, session, url_for, send_from_directory
from run_code import execute_code
from database import (
    create_user, get_user, verify_password, log_user_activity,
    get_recent_activities, save_code, get_recent_codes
)
import secrets
import os

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = secrets.token_hex(32)
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
#home route
@app.route('/')
def home():
    return render_template('home.html', username=session.get("username"))
#files 
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOADS_DIR, filename)

from flask import session, redirect, url_for, render_template
#code editor route
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

#html editor route
@app.route('/editor')
def html_editor():
    return render_template('web-editor/weditor.html')
#signup
@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json(force=True)  

    full_name = data.get("fullName")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not full_name or not username or not email or not password:
        return jsonify({"message": "All fields are required!"}), 400

    result, status = create_user(full_name, username, email, password)  # Pass email

    if status == 201:
        session["username"] = username
        session["full_name"] = full_name
        log_user_activity(username, "Signed Up")

    return jsonify(result), status

#login
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/auth/login', methods=['POST'])
def authenticate():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return render_template("login.html", error="Both username and password are required!")

    user = get_user(username)

    if not user:
        return render_template("login.html", error="No user found with this username!")

    if not verify_password(user["password"], password):
        return render_template("login.html", error="Invalid password!")

    session["username"] = username  
    session["full_name"] = user["full_name"]  
    log_user_activity(username, "Logged In")

    return redirect(url_for('index'))  

#profile page route
@app.route('/profile')
def profile():
    if "username" not in session:
        return redirect(url_for("login_page"))

    username = session["username"]
    activities = get_recent_activities(username)
    codes = get_recent_codes(username)

    return render_template("profile.html", full_name=session["full_name"], username=username, activities=activities, codes=codes)
@app.route('/project')#project page route
def project():
    if "username" not in session:
        return redirect(url_for("login_page"))

    username = session["username"]
    codes = get_recent_codes(username)

    return render_template("project.html", full_name=session["full_name"], username=username, codes=codes)
#logout
@app.route('/logout')
def logout():
    if "username" in session:
        log_user_activity(session["username"], "Logged Out")
    session.clear()  
    return redirect(url_for("home"))

#code execution logic route
@app.route('/run', methods=['POST'])
def run_code():
    if "username" not in session:
        return jsonify({"message": "You must be logged in to run code!"}), 401

    username = session["username"]
    data = request.get_json(force=True)
    language = data.get("language")
    code = data.get("code")
    userInput = data.get("input", "")

    try:
        output = execute_code(language, code, userInput)

        # user's log activity
        log_user_activity(username, f"Ran {language} code")
        save_code(username, code, language)


        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"output": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5500)