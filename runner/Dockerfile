ARG RUNNER_BASE=python:3.12-bookworm
FROM ${RUNNER_BASE}

COPY python-requirements.txt /opt/codesphere/python-requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends libeigen3-dev nlohmann-json3-dev \
    && python -m pip install --no-cache-dir -r /opt/codesphere/python-requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY runner.py /opt/codesphere/runner.py
COPY interactive.py /opt/codesphere/interactive.py

ENV PYTHONDONTWRITEBYTECODE=1
ENV MPLCONFIGDIR=/tmp/matplotlib
USER 65534:65534
ENTRYPOINT ["python", "-I", "/opt/codesphere/runner.py"]
