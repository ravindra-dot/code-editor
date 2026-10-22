"""Short-lived Docker terminal sessions for the editor."""

import codecs
import json
import subprocess
import threading
import time
import uuid

from run_code import docker_command, validate_source, _remove_container

MAX_OUTPUT = 64 * 1024
MAX_INPUT = 16 * 1024
MAX_DURATION = 105
sessions = {}
sessions_lock = threading.Lock()


class TerminalSession:
    def __init__(self, owner, language, code):
        validate_source(language, code)
        self.id = uuid.uuid4().hex
        self.owner = owner
        self.language = language
        self.code = code
        self.container_name = f"codesphere-terminal-{self.id}"
        self.output = bytearray()
        self.lock = threading.Lock()
        self.input_lock = threading.Lock()
        self.done = False
        self.stopped = False
        self.created = time.monotonic()
        self.process = subprocess.Popen(
            docker_command(self.container_name, interactive=True),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0,
        )
        try:
            header = json.dumps({"language": language, "code": code}).encode() + b"\n"
            self.process.stdin.write(header)
        except OSError:
            pass
        threading.Thread(target=self._run, daemon=True).start()

    def _append(self, chunk):
        with self.lock:
            remaining = MAX_OUTPUT - len(self.output)
            self.output.extend(chunk[:remaining])
            exceeded = len(chunk) > remaining
        if exceeded:
            self.stop("\r\nOutput limit exceeded\r\n")

    def _drain(self, stream):
        while chunk := stream.read(4096):
            self._append(chunk)

    def _run(self):
        readers = [
            threading.Thread(target=self._drain, args=(self.process.stdout,), daemon=True),
            threading.Thread(target=self._drain, args=(self.process.stderr,), daemon=True),
        ]
        for reader in readers:
            reader.start()
        try:
            self.process.wait(timeout=MAX_DURATION)
        except subprocess.TimeoutExpired:
            self.stop("\r\nExecution timed out\r\n")
        for reader in readers:
            reader.join(timeout=2)
        with self.lock:
            self.done = True
        try:
            self.process.stdin.close()
            self.process.stdout.close()
            self.process.stderr.close()
        except OSError:
            pass

    def send(self, data):
        if not isinstance(data, str) or len(data.encode("utf-8")) > MAX_INPUT:
            raise ValueError("Input must be text up to 16 KiB")
        with self.input_lock:
            if self.done or self.stopped:
                raise ValueError("Program has finished")
            try:
                self.process.stdin.write(data.encode("utf-8"))
            except OSError as error:
                raise ValueError("Program has finished") from error

    def stop(self, message="\r\nStopped\r\n"):
        with self.lock:
            if self.stopped or self.done:
                return
            self.stopped = True
            remaining = MAX_OUTPUT - len(self.output)
            self.output.extend(message.encode()[:remaining])
        self.process.kill()
        _remove_container(self.container_name)

    def snapshot(self, offset):
        with self.lock:
            if offset < 0 or offset > len(self.output):
                raise ValueError("Invalid output offset")
            decoder = codecs.getincrementaldecoder("utf-8")("replace")
            output = decoder.decode(bytes(self.output[offset:]), final=self.done)
            pending = len(decoder.getstate()[0])
            return {
                "output": output,
                "offset": len(self.output) - pending,
                "done": self.done,
            }


def create_session(owner, language, code):
    with sessions_lock:
        expired = [key for key, item in sessions.items() if item.done and time.monotonic() - item.created > 300]
        for key in expired:
            del sessions[key]
        active = sum(not item.done for item in sessions.values())
        if active >= 8:
            raise ValueError("Too many programs are running")
        if sum(not item.done and item.owner == owner for item in sessions.values()) >= 2:
            raise ValueError("Too many programs are running in this browser")
        item = TerminalSession(owner, language, code)
        sessions[item.id] = item
        return item


def get_session(session_id, owner):
    with sessions_lock:
        item = sessions.get(session_id)
    if item is None or item.owner != owner:
        return None
    return item
