import subprocess
import os
import sys

BLOCKED_COMMANDS = [
    "os.system", 
    "subprocess.call", 
    "shutil.rmtree", 
    "exec", 
    "eval", 
    "open('/etc/passwd'", 
    "sys.exit"
]

def is_safe_code(code):
    """Check if the code contains blocked commands"""
    for cmd in BLOCKED_COMMANDS:
        if cmd in code:
            return False, f"Security Alert: Use of restricted command '{cmd}' detected!"
    return True, "Code is safe to execute."

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

def execute_code(language, code, user_input):
    filename_map = {
        "python": "script.py",
        "c": "program.c",
        "cpp": "program.cpp"
    }

    if language not in filename_map:
        raise ValueError("Unsupported language")

    filename = os.path.join(UPLOADS_DIR, filename_map[language])

    with open(filename, "w") as f:
        f.write(code)

    if language == "python":
        command = [sys.executable, filename]
    elif language in ["c", "cpp"]:
        binary_file = os.path.join(UPLOADS_DIR, "program")
        compiler = "gcc" if language == "c" else "g++"

        compile_process = subprocess.run([compiler, filename, "-o", binary_file], capture_output=True, text=True)
        if compile_process.returncode != 0:
            return compile_process.stderr.strip()

        command = [binary_file]

    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=user_input)

    return stderr.strip() if stderr else stdout.strip()