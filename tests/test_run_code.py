import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import run_code


class DockerRunnerTests(unittest.TestCase):
    @patch.object(run_code, "_run_limited")
    def test_code_is_sent_to_restricted_container(self, run):
        run.return_value = (0, "Hello\n")

        output = run_code.execute_code("python", "print('Hello')", "sample input")

        self.assertEqual(output, "Hello")
        args, _ = run.call_args
        command = args[0]
        self.assertEqual(command[:2], ["docker", "run"])
        self.assertIn("--network", command)
        self.assertEqual(command[command.index("--network") + 1], "none")
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop", command)
        self.assertIn("--memory", command)
        self.assertIn("--pids-limit", command)
        self.assertNotIn("--volume", command)
        self.assertNotIn("--mount", command)
        self.assertEqual(command[-1], run_code.RUNNER_IMAGE)
        self.assertEqual(json.loads(args[1]), {
            "language": "python", "code": "print('Hello')", "input": "sample input"
        })
        self.assertEqual(args[2], command[command.index("--name") + 1])

    @patch.object(run_code, "_run_limited")
    def test_invalid_request_never_starts_docker(self, run):
        with self.assertRaises(ValueError):
            run_code.execute_code("javascript", "alert(1)", "")
        with self.assertRaises(ValueError):
            run_code.execute_code("python", "x" * (run_code.MAX_CODE_BYTES + 1), "")
        run.assert_not_called()

    @patch.object(run_code, "_remove_container")
    def test_timeout_removes_named_container(self, remove):
        command = [sys.executable, "-c", "import time; time.sleep(1)"]
        with patch.object(run_code, "DOCKER_TIMEOUT_SECONDS", 0.05):
            with self.assertRaises(run_code.RunnerTimeoutError):
                run_code._run_limited(command, "", "test-container")
        remove.assert_called_once_with("test-container")

    @patch.object(run_code, "_remove_container")
    def test_host_caps_output_even_if_runner_is_bypassed(self, remove):
        command = [sys.executable, "-c", "print('x' * 70000)"]
        with self.assertRaises(run_code.RunnerOutputLimitError):
            run_code._run_limited(command, "", "test-container")
        remove.assert_called_once_with("test-container")

    @patch.object(run_code, "_run_limited")
    def test_missing_docker_reports_unavailable(self, run):
        run.side_effect = FileNotFoundError("docker")
        with self.assertRaises(run_code.RunnerUnavailableError):
            run_code.execute_code("python", "print(1)", "")


if __name__ == "__main__":
    unittest.main()
