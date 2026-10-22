# Container runner guidance

`Dockerfile` builds the Linux image used by `backend/run_code.py`. `runner.py` receives one JSON request on stdin, writes source into `/work`, compiles C/C++ when needed, and runs the program. The image is built with `docker build --pull -t codesphere-runner:latest ./runner` from the repository root.

The default base is the full `python:3.12-bookworm` image, which includes GCC and G++. `RUNNER_BASE` can be overridden for a cached local image when offline; rebuild against the default when connectivity returns.

- Keep the Dockerfile entry point and the JSON fields (`language`, `code`, `input`) aligned with `backend/run_code.py`.
- The host supplies Docker restrictions: no network or host mounts, read-only image filesystem, non-root user, dropped capabilities, limited tmpfs, memory, CPU, process count, and an outer timeout. Do not weaken them when changing the runner.
- Keep compilation and program timeouts and bounded output inside the image. Every request runs in a fresh container, so scratch files may use fixed names without sharing state.
- Avoid running untrusted sample code during verification. Rebuild the image after editing either file, then check a small trusted program in each supported language.
