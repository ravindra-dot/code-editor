"""Bridge Docker stdin/stdout to an interactive program on a Linux PTY."""

import json
import os
import pty
import select
import signal
import subprocess
import sys
import time

MAX_OUTPUT = 64 * 1024
RUN_SECONDS = 90


def write(data):
    os.write(1, data)


def read_header():
    header = bytearray()
    while len(header) <= 80 * 1024:
        char = os.read(0, 1)
        if not char:
            raise ValueError("Missing program")
        if char == b"\n":
            return json.loads(header)
        header.extend(char)
    raise ValueError("Program is too large")


def main():
    payload = read_header()
    language = payload["language"]
    code = payload["code"]
    if language not in ("python", "c", "cpp") or not isinstance(code, str):
        raise ValueError("Invalid program")
    extension = {"python": "py", "c": "c", "cpp": "cpp"}[language]
    source = f"/work/main.{extension}"
    with open(source, "w", encoding="utf-8") as file:
        file.write(code)
    if language != "python":
        compiler = "gcc" if language == "c" else "g++"
        try:
            result = subprocess.run(
                [compiler, source, "-o", "/work/program"],
                capture_output=True, timeout=10, check=False,
            )
        except subprocess.TimeoutExpired:
            write(b"Compilation timed out\r\n")
            return
        if result.returncode:
            write((result.stdout + result.stderr)[:MAX_OUTPUT])
            return
    argv = ["python", "-u", "-I", source] if language == "python" else ["/work/program"]
    pid, master = pty.fork()
    if pid == 0:
        os.execvp(argv[0], argv)
    output_size = 0
    deadline = time.monotonic() + RUN_SECONDS
    child_done = False
    try:
        while True:
            if not child_done:
                child, _ = os.waitpid(pid, os.WNOHANG)
                child_done = bool(child)
            if child_done:
                # Drain the PTY before reporting completion.
                readable, _, _ = select.select([master], [], [], 0.1)
                if not readable:
                    break
            if time.monotonic() >= deadline:
                os.killpg(pid, signal.SIGKILL)
                write(b"\r\nExecution timed out\r\n")
                break
            readable, _, _ = select.select(([master] if child_done else [0, master]), [], [], 0.1)
            if 0 in readable:
                incoming = os.read(0, 4096)
                if incoming:
                    try:
                        os.write(master, incoming)
                    except OSError:
                        pass
            if master in readable:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                output_size += len(chunk)
                if output_size > MAX_OUTPUT:
                    os.killpg(pid, signal.SIGKILL)
                    write(b"\r\nOutput limit exceeded\r\n")
                    break
                write(chunk)
    finally:
        os.close(master)
        if not child_done:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        write((str(error) + "\r\n").encode())
