# Contributing to CodeSphere

Thanks for helping improve CodeSphere. Please keep changes focused and describe the behavior they change.

## Before you start

- Search existing issues and pull requests for the same problem.
- For a bug, include the route or editor, steps to reproduce, expected result, actual result, and relevant error output. Remove passwords, tokens, and personal data from logs.
- For a feature, explain the user need and how it fits the current single-program editor.
- Report security issues privately as described in [SECURITY.md](SECURITY.md).

## Local development

Follow the [quick start](README.md#quick-start), then run:

```powershell
python -B -m unittest discover -s tests -v
```

Changes to the Docker runner should preserve its isolation and resource limits. When Docker is available, rebuild the image and run `tests/docker_smoke.py` and `tests/interactive_smoke.py` with small, trusted programs. Keep `data/`, local environments, generated programs, and credentials out of commits.

## Pull requests

Explain the change, how you tested it, and any limits of the test. If you change a route or JSON field, update its frontend caller. If you change a page, include a screenshot when it helps reviewers see the result.
