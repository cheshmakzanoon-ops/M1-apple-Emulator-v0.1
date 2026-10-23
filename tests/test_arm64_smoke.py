"""Regressions for P005's explicit TCG choice and honest generic-smoke results."""

import contextlib
import io
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from unittest import mock

from tools import run_arm64_smoke as smoke


class SmokeExecutorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.guest = Path(self.directory.name) / "guest payload;$(echo nope).elf"
        self.guest.write_bytes(b"test fixture; QEMU is mocked")
        self.output = (smoke.EXPECTED + "\n").encode()

    def invoke(self, process=None, *, tool="/tools/qemu-system-aarch64", args=None,
               launch_error=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        arguments = [str(self.guest)] if args is None else args
        with (mock.patch("sys.argv", ["run_arm64_smoke.py", *arguments]),
              mock.patch.object(smoke.shutil, "which", return_value=tool),
              mock.patch.object(smoke.subprocess, "Popen", return_value=process,
                                side_effect=launch_error) as launch,
              contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr)):
            status = smoke.main()
        return status, stdout.getvalue(), stderr.getvalue(), launch

    def process(self, *, output=None, returncode=0, timeout=False):
        process = mock.Mock()
        process.returncode = returncode
        result = (self.output if output is None else output, None)
        if timeout:
            process.communicate.side_effect = [subprocess.TimeoutExpired("qemu", 8), result]
        else:
            process.communicate.return_value = result
        return process

    def test_executor_is_tcg_without_hypervisor_fallback(self):
        argv = smoke.command("qemu-system-aarch64", self.guest)
        self.assertEqual(argv.count("-accel"), 1)
        self.assertEqual(argv[argv.index("-accel") + 1], "tcg")
        self.assertNotIn("-enable-kvm", argv)
        self.assertEqual(argv[argv.index("-M") + 1], "virt")
        self.assertEqual(argv[argv.index("-cpu") + 1], "cortex-a57")
        self.assertEqual(argv[argv.index("-smp") + 1], "1")

    def test_marker_and_clean_exit_pass_with_non_m1_label(self):
        process = self.process()
        status, stdout, stderr, _ = self.invoke(process)
        self.assertEqual(status, 0)
        self.assertIn("with TCG", stdout)
        self.assertIn("does not implement or prove Apple M1 emulation", stdout)
        self.assertEqual(stderr, "")
        process.kill.assert_not_called()

    def test_looping_guest_marker_passes_after_runner_timeout_kill(self):
        process = self.process(returncode=-signal.SIGKILL, timeout=True)
        status, stdout, stderr, _ = self.invoke(process)
        self.assertEqual(status, 0)
        self.assertIn("PASS:", stdout)
        self.assertEqual(stderr, "")
        process.kill.assert_called_once_with()
        self.assertEqual(process.communicate.call_args_list, [mock.call(timeout=8.0), mock.call()])

    def test_clean_exit_without_marker_fails(self):
        status, stdout, stderr, _ = self.invoke(self.process(output=b""))
        self.assertEqual(status, 1)
        self.assertNotIn("PASS:", stdout)
        self.assertIn("smoke test failed", stderr)

    def test_timeout_without_marker_fails(self):
        process = self.process(output=b"unrelated console text\n",
                               returncode=-signal.SIGKILL, timeout=True)
        status, stdout, stderr, _ = self.invoke(process)
        self.assertEqual(status, 1)
        self.assertNotIn("PASS:", stdout)
        self.assertIn("unrelated console text", stderr)

    def test_tcg_initialization_failure_is_not_retried_with_another_accelerator(self):
        process = self.process(output=b"invalid accelerator tcg\n", returncode=1)
        status, stdout, stderr, launch = self.invoke(process)
        self.assertEqual(status, 1)
        self.assertNotIn("PASS:", stdout)
        self.assertIn("invalid accelerator tcg", stderr)
        launch.assert_called_once()

    def test_nonzero_exit_after_marker_fails(self):
        for returncode in (1, 2, -signal.SIGTERM, -signal.SIGKILL):
            with self.subTest(returncode=returncode):
                status, stdout, stderr, _ = self.invoke(self.process(returncode=returncode))
                self.assertEqual(status, 1)
                self.assertNotIn("PASS:", stdout)
                self.assertIn(f"status {returncode}", stderr)

    def test_non_kill_error_racing_with_timeout_fails(self):
        process = self.process(returncode=1, timeout=True)
        status, stdout, stderr, _ = self.invoke(process)
        self.assertEqual(status, 1)
        self.assertNotIn("PASS:", stdout)
        self.assertIn("status 1", stderr)

    def test_missing_qemu_reports_dependency_and_does_not_launch(self):
        status, stdout, stderr, launch = self.invoke(tool=None)
        self.assertEqual(status, 2)
        self.assertNotIn("PASS:", stdout)
        self.assertIn("Missing qemu-system-aarch64", stderr)
        launch.assert_not_called()

    def test_missing_guest_does_not_launch(self):
        status, _, stderr, launch = self.invoke(args=[str(self.guest.with_name("absent.elf"))])
        self.assertEqual(status, 2)
        self.assertIn("Missing guest ELF", stderr)
        launch.assert_not_called()

    def test_directory_cannot_be_used_as_guest_elf(self):
        status, _, stderr, launch = self.invoke(args=[self.directory.name])
        self.assertEqual(status, 2)
        self.assertIn("Missing guest ELF", stderr)
        launch.assert_not_called()

    def test_launch_error_is_reported_without_traceback(self):
        status, stdout, stderr, launch = self.invoke(launch_error=PermissionError("not executable"))
        self.assertEqual(status, 2)
        self.assertEqual(stdout, "")
        self.assertIn("Cannot launch", stderr)
        self.assertIn("not executable", stderr)
        launch.assert_called_once()

    def test_elf_path_is_one_argument_without_shell_interpretation(self):
        status, _, _, launch = self.invoke(self.process())
        self.assertEqual(status, 0)
        argv = launch.call_args.args[0]
        self.assertIsInstance(argv, list)
        self.assertEqual(argv[argv.index("-kernel") + 1], str(self.guest.resolve()))
        self.assertFalse(launch.call_args.kwargs.get("shell", False))
        self.assertEqual(launch.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_positive_timeout_reaches_process(self):
        process = self.process()
        status, _, _, _ = self.invoke(process, args=[str(self.guest), "--timeout", "0.25"])
        self.assertEqual(status, 0)
        process.communicate.assert_called_once_with(timeout=0.25)

    def test_maximum_timeout_is_accepted(self):
        process = self.process()
        status, _, _, _ = self.invoke(process, args=[str(self.guest), "--timeout", "300"])
        self.assertEqual(status, 0)
        process.communicate.assert_called_once_with(timeout=300.0)

    def test_invalid_timeout_is_rejected_before_launch(self):
        for value in ("0", "-1", "nan", "inf", "-inf", "1e309", "nonsense",
                      "300.000001", "301", "1e100"):
            with self.subTest(value=value):
                with (mock.patch("sys.argv", ["run_arm64_smoke.py", str(self.guest),
                                              f"--timeout={value}"]),
                      mock.patch.object(smoke.subprocess, "Popen") as launch,
                      contextlib.redirect_stderr(io.StringIO()) as stderr,
                      self.assertRaises(SystemExit) as caught):
                    smoke.main()
                self.assertEqual(caught.exception.code, 2)
                self.assertIn("timeout must be finite and greater than zero", stderr.getvalue())
                self.assertIn("at most 300 seconds", stderr.getvalue())
                launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
