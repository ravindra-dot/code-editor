"""Container entry point. The request arrives as JSON on stdin."""

import json
import subprocess
import sys


SOURCE_FILES = {"python": "script.py", "c": "program.c", "cpp": "program.cpp"}
OUTPUT_LIMIT = 64 * 1024
COMPILE_TIMEOUT = 10
RUN_TIMEOUT = 5


def _run(command, input_text, timeout):
    # Output files reside on the size-limited /work tmpfs. Only the first
    # OUTPUT_LIMIT bytes are returned to the web app.
    with open("stdout.txt", "w+b") as stdout_file, open("stderr.txt", "w+b") as stderr_file:
        try:
            result = subprocess.run(
                command, input=input_text.encode("utf-8"),
                stdout=stdout_file, stderr=stderr_file, timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None, "Time limit exceeded"
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read(OUTPUT_LIMIT).decode("utf-8", errors="replace")
        stderr = stderr_file.read(OUTPUT_LIMIT).decode("utf-8", errors="replace")
    return result.returncode, (stderr or stdout).rstrip("\n")


def main():
    request = json.load(sys.stdin)
    language = request["language"]
    filename = SOURCE_FILES[language]
    with open(filename, "w", encoding="utf-8") as source_file:
        source_file.write(request["code"])

    if language == "python":
        _, output = _run([sys.executable, "-I", filename], request["input"], RUN_TIMEOUT)
    else:
        compiler = "gcc" if language == "c" else "g++"
        compile_status, compile_output = _run(
            [compiler, filename, "-I/usr/include/eigen3", "-o", "program"], "", COMPILE_TIMEOUT
        )
        if compile_status != 0:
            output = compile_output or "Compilation failed"
        else:
            _, output = _run(["./program"], request["input"], RUN_TIMEOUT)
    sys.stdout.write(output[:OUTPUT_LIMIT])


if __name__ == "__main__":
    main()
