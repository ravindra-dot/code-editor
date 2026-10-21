ARG RUNNER_BASE=python:3.12-bookworm
FROM ${RUNNER_BASE}

COPY runner.py /opt/codesphere/runner.py
COPY interactive.py /opt/codesphere/interactive.py

ENV PYTHONDONTWRITEBYTECODE=1
USER 65534:65534
ENTRYPOINT ["python", "-I", "/opt/codesphere/runner.py"]
