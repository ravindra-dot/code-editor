"""Run submitted code in a short-lived, restricted Docker container."""

import json
import subprocess
import threading
import uuid


RUNNER_IMAGE = "codesphere-runner:latest"
MAX_CODE_BYTES = 64 * 1024
MAX_INPUT_BYTES = 16 * 1024
DOCKER_TIMEOUT_SECONDS = 30
MAX_HOST_OUTPUT_BYTES = 64 * 1024


class RunnerUnavailableError(RuntimeError):
    """The local Docker runner cannot be started."""


class RunnerTimeoutError(RuntimeError):
    """The Docker command exceeded its deadline."""


class RunnerOutputLimitError(ValueError):
    """The program produced too much output."""


def execute_code(language, code, user_input):
    validate_source(language, code)
    if not isinstance(code, str) or not isinstance(user_input, str):
        raise ValueError("Code and input must be text")
    if len(user_input.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError("Input is too large (16 KiB maximum)")

    container_name = f"codesphere-run-{uuid.uuid4().hex}"
    command = docker_command(container_name)
    payload = json.dumps({"language": language, "code": code, "input": user_input})
    try:
        returncode, stdout = _run_limited(command, payload, container_name)
    except FileNotFoundError as exc:
        raise RunnerUnavailableError("Docker CLI was not found on PATH") from exc

    if returncode != 0:
        raise RunnerUnavailableError(
            "Docker runner unavailable. Start Docker Desktop and build the runner image (see README)."
        )
    return stdout.rstrip("\n")


def validate_source(language, code):
    if language not in ("python", "c", "cpp"):
        raise ValueError("Unsupported language")
    if not isinstance(code, str):
        raise ValueError("Code must be text")
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise ValueError("Code is too large (64 KiB maximum)")


def docker_command(container_name, interactive=False):
    command = [
        "docker", "run", "--rm", "--interactive", "--pull=never",
        "--name", container_name,
        "--network", "none",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true",
        "--user", "65534:65534",
        "--memory", "512m", "--memory-swap", "512m",
        "--cpus", "1", "--pids-limit", "64",
        "--tmpfs", "/work:rw,exec,nosuid,nodev,size=32m,mode=1777",
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m,mode=1777",
        "--workdir", "/work",
    ]
    if interactive:
        command.extend(["--entrypoint", "python"])
    command.append(RUNNER_IMAGE)
    if interactive:
        command.extend(["-I", "/opt/codesphere/interactive.py"])
    return command


def _run_limited(command, payload, container_name):
    """Drain Docker output with a host-side cap, including attempts to bypass runner limits."""
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout = bytearray()
    stderr = bytearray()
    output_exceeded = threading.Event()

    def drain(stream, destination, limit):
        while chunk := stream.read(4096):
            remaining = limit - len(destination)
            if remaining > 0:
                destination.extend(chunk[:remaining])
            if len(chunk) > remaining:
                output_exceeded.set()
                try:
                    process.kill()
                except OSError:
                    pass
                break

    def feed():
        try:
            process.stdin.write(payload.encode("utf-8"))
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    workers = [
        threading.Thread(target=drain, args=(process.stdout, stdout, MAX_HOST_OUTPUT_BYTES), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, stderr, 8 * 1024), daemon=True),
        threading.Thread(target=feed, daemon=True),
    ]
    for worker in workers:
        worker.start()
    try:
        returncode = process.wait(timeout=DOCKER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait()
        _remove_container(container_name)
        raise RunnerTimeoutError("Code execution timed out") from exc
    finally:
        for worker in workers:
            worker.join(timeout=1)
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()

    if output_exceeded.is_set():
        _remove_container(container_name)
        raise RunnerOutputLimitError("Output limit exceeded (64 KiB maximum)")
    return returncode, stdout.decode("utf-8", errors="replace")


def _remove_container(name):
    """Remove a container left behind if the Docker client times out."""
    try:
        subprocess.run(
            ["docker", "rm", "--force", name],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
