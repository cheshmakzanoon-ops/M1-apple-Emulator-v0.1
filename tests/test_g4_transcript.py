"""Synthetic protocol tests only; these fixtures are not G4 or hardware evidence."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

from tools import check_g4_transcript as witness

ROOT = Path(__file__).resolve().parents[1]
NONCE = "0123456789abcdef0123456789abcdef"
LEFT, RIGHT = 731, 29


def synthetic_transcript() -> str:
    """Artificial Linux-shaped text, explicitly not an observed boot capture."""
    return f"""Linux version SYNTHETIC-FIXTURE-NOT-A-BOOT
# /bin/sh /g4-probe.sh {NONCE}
G4-BEGIN {NONCE}
G4-ARCH aarch64
G4-TTY /dev/ttySAC0
G4-DRIVER samsung-uart
G4-COMPAT-BEGIN
apple,j274
apple,t8103
apple,arm-platform
G4-COMPAT-END
G4-CONSOLES-BEGIN
ttySAC0              -W- (EC  a) 204:64
G4-CONSOLES-END
G4-IRQ-BEFORE-BEGIN
           CPU0
 17:         10     AIC 605 Level 235200000.serial
 18:         50 AIC-FIQ   0 Level arch_timer
IPI0:         0       Rescheduling interrupts
Err:          0
G4-IRQ-BEFORE-END
G4-UPTIME-BEFORE 10.25 19.00
G4-READY {NONCE}
G4-IRQ-AFTER-BEGIN
           CPU0
 17:         12     AIC 605 Level 235200000.serial
 18:         60 AIC-FIQ   0 Level arch_timer
IPI0:         0       Rescheduling interrupts
Err:          0
G4-IRQ-AFTER-END
G4-UPTIME-AFTER 11.25 20.00
G4-RESULT {NONCE} {LEFT + RIGHT}
G4-END {NONCE}
# [ \"$?\" -eq 0 ] && printf '\\nG4-SHELL %s %s\\n' {NONCE} \"$(({LEFT} * {RIGHT}))\"
G4-SHELL {NONCE} {LEFT * RIGHT}
# """


class G4TranscriptTests(unittest.TestCase):
    def validate(self, text, nonce=NONCE, left=LEFT, right=RIGHT):
        return witness.validate_transcript(text, nonce, left, right)

    def test_synthetic_complete_protocol_and_crlf_pass(self):
        self.assertEqual(self.validate(synthetic_transcript()), [])
        self.assertEqual(self.validate(synthetic_transcript().replace("\n", "\r\n")), [])

    def test_runtime_assigned_irq_numbers_are_supported(self):
        text = synthetic_transcript().replace(" 17:", " 123:").replace("AIC 605", "AIC 131677")
        self.assertEqual(self.validate(text), [])

    def test_irq_counter_and_hwirq_source_type_boundaries_are_distinct(self):
        maximum = (1 << 32) - 1
        for old_before, old_after in ((" 10 ", " 12 "), (" 50 ", " 60 ")):
            with self.subTest(counter=old_after):
                text = synthetic_transcript().replace(old_before, f" {maximum - 1} ")
                self.assertEqual(self.validate(text.replace(old_after, f" {maximum} ")), [])
                self.assertTrue(self.validate(text.replace(old_after, f" {maximum + 1} ")))
        text = synthetic_transcript().replace("AIC 605", f"AIC {(1 << 64) - 1}")
        self.assertEqual(self.validate(text), [])
        self.assertTrue(self.validate(text.replace(str((1 << 64) - 1), str(1 << 64))))

    def test_irq_optional_level_and_handler_description_match_kernel_format(self):
        for old, new in (("Level ", ""), ("Level ", "Level -fasteoi "), ("Level ", "-percpu_devid ")):
            with self.subTest(metadata=new):
                self.assertEqual(self.validate(synthetic_transcript().replace(old, new)), [])

    def test_irq_hwirq_and_optional_metadata_must_be_well_formed(self):
        for old, new in (("AIC 605", "AIC nonsense"), ("AIC 605", "AIC -1"),
                         ("AIC 605", "AIC 0605"), ("AIC 605", "AIC 18446744073709551616"),
                         ("AIC 605 Level", "AIC Level bogus"),
                         ("Level 235200000.serial", "nonsense 235200000.serial"),
                         ("Level arch_timer", "Level Edge arch_timer")):
            with self.subTest(change=(old, new)):
                self.assertTrue(self.validate(synthetic_transcript().replace(old, new)))

    def test_expected_challenge_parameters_are_strict(self):
        for nonce in (None, [], "", "0" * 31, "0" * 33, "A" * 32, "g" * 32, NONCE + "\n"):
            with self.subTest(nonce=nonce):
                self.assertTrue(self.validate(synthetic_transcript(), nonce=nonce))
        for value in (None, [], "1", 0, -1, 1000000, True, 1.0):
            with self.subTest(operand=value):
                self.assertTrue(self.validate(synthetic_transcript(), left=value))
                self.assertTrue(self.validate(synthetic_transcript(), right=value))

    def test_no_prompt_echo_or_static_marker_substitutes_for_protocol(self):
        for text in ("", "BusyBox\n# ", f"# echo G4-RESULT {NONCE} {LEFT + RIGHT}\n",
                     f"G4-RESULT {NONCE} {LEFT + RIGHT}\n", "ARM64 baseline OK\n"):
            with self.subTest(text=text):
                self.assertTrue(self.validate(text))

    def test_fresh_expected_nonce_and_computed_answer_are_required(self):
        text = synthetic_transcript()
        self.assertTrue(self.validate(text, nonce="f" * 32))
        self.assertTrue(self.validate(text, right=RIGHT + 1))
        for old, new in ((f"G4-READY {NONCE}", "G4-READY " + "f" * 32),
                         (f"G4-RESULT {NONCE} {LEFT + RIGHT}", f"G4-RESULT {NONCE} 0")):
            with self.subTest(old=old):
                self.assertTrue(self.validate(text.replace(old, new)))

    def test_every_frame_is_required_once_and_in_order(self):
        lines = synthetic_transcript().splitlines(keepends=True)
        for index, line in enumerate(lines):
            if not line.startswith("G4-"):
                continue
            for operation in ("remove", "duplicate", "move", "prefix"):
                altered = list(lines)
                if operation == "remove":
                    altered.pop(index)
                elif operation == "duplicate":
                    altered.insert(index, line)
                elif operation == "move":
                    altered.insert(0, altered.pop(index))
                else:
                    altered[index] = "# " + line
                with self.subTest(frame=line.strip(), operation=operation):
                    # Moving the very first frame ahead of harmless preamble is
                    # equivalent, not a change of protocol frame ordering.
                    if operation == "move" and line.startswith("G4-BEGIN "):
                        continue
                    self.assertTrue(self.validate("".join(altered)))

    def test_second_trial_and_unknown_protocol_frames_are_rejected(self):
        text = synthetic_transcript()
        for changed in (text + "\n" + text, "G4-UNKNOWN\n" + text,
                        text + "\nG4-UNKNOWN\n", text.replace("G4-READY", "G4-UNKNOWN\nG4-READY")):
            with self.subTest(text=changed[:80]):
                self.assertTrue(self.validate(changed))

    def test_architecture_console_driver_and_ordered_identity_are_required(self):
        for old, new in (("G4-ARCH aarch64", "G4-ARCH x86_64"),
                         ("G4-TTY /dev/ttySAC0", "G4-TTY /dev/ttyAMA0"),
                         ("G4-DRIVER samsung-uart", "G4-DRIVER uart-pl011"),
                         ("apple,j274\napple,t8103", "apple,t8103\napple,j274"),
                         ("apple,j274", "apple,j293"), ("apple,arm-platform\n", ""),
                         ("ttySAC0              -W-", "ttyAMA0              -W-"),
                         ("-W- (EC  a)", "--- (EC  a)"), ("-W- (EC  a)", "-W- ( C  a)")):
            with self.subTest(change=(old, new)):
                self.assertTrue(self.validate(synthetic_transcript().replace(old, new)))

    def test_console_rows_cannot_be_duplicated_or_fabricated_without_raw_format(self):
        row = "ttySAC0              -W- (EC  a) 204:64"
        for new in (row + "\n" + row, "ttySAC0", "ttySAC0 -W- (EC) device"):
            with self.subTest(new=new):
                self.assertTrue(self.validate(synthetic_transcript().replace(row, new)))

    def test_uart_irq_and_timer_fiq_rows_must_both_advance(self):
        for old, new in ((" 12 ", " 10 "), (" 60 ", " 50 "), (" 12 ", " 9 "), (" 60 ", " 49 "),
                         ("AIC-FIQ", "AIC"), ("235200000.serial", "ttySAC0"),
                         ("arch_timer", "virtio0"), ("AIC 605", "GIC 605")):
            with self.subTest(change=(old, new)):
                self.assertTrue(self.validate(synthetic_transcript().replace(old, new)))

    def test_irq_identities_and_cpu_columns_cannot_change_mid_trial(self):
        text = synthetic_transcript()
        for old, new in ((" 17:", " 19:"), ("AIC 605", "AIC 606"), ("CPU0", "CPU2"),
                         ("Level arch_timer", "Edge arch_timer")):
            position = text.index("G4-IRQ-AFTER-BEGIN")
            altered = text[:position] + text[position:].replace(old, new)
            with self.subTest(change=(old, new)):
                self.assertTrue(self.validate(altered))

    def test_malformed_irq_headers_counters_and_duplicate_sources_fail(self):
        for old, new in (("CPU0", ""), ("CPU0", "CPU1 CPU0"), ("CPU0", "CPU0 CPU0"),
                         ("CPU0", "CPU0 CPU1"), (" 12 ", " -1 "), (" 12 ", " 1.2 "),
                         (" 12 ", " "), (" 12 ", " 18446744073709551616 ")):
            with self.subTest(change=(old, new)):
                self.assertTrue(self.validate(synthetic_transcript().replace(old, new)))
        for row in (" 17:         12     AIC 605 Level 235200000.serial",
                    " 18:         60 AIC-FIQ   0 Level arch_timer"):
            self.assertTrue(self.validate(synthetic_transcript().replace(row, row + "\n" + row)))

    def test_uptime_requires_a_completed_scheduled_second(self):
        for value in ("11.24 20.00", "10.25 20.00", "9.25 20.00", "nan 20.00", "inf 20.00",
                      "11.25", "11.25 nope", "11.250 20.00", "-11.25 20.00"):
            with self.subTest(uptime=value):
                self.assertTrue(self.validate(synthetic_transcript().replace("11.25 20.00", value)))

    def test_separate_interactive_shell_command_must_compute_the_product(self):
        expected = f"G4-SHELL {NONCE} {LEFT * RIGHT}"
        for replacement in ("", "# " + expected, f"G4-SHELL {NONCE} {LEFT + RIGHT}",
                            f"G4-SHELL {NONCE} $(({LEFT} * {RIGHT}))"):
            with self.subTest(replacement=replacement):
                self.assertTrue(self.validate(synthetic_transcript().replace(expected, replacement)))

    def test_challenge_operand_boundaries_are_valid(self):
        for left, right in ((1, 1), (999999, 999999)):
            text = synthetic_transcript().replace(f"G4-RESULT {NONCE} {LEFT + RIGHT}",
                                                  f"G4-RESULT {NONCE} {left + right}")
            text = text.replace(f"G4-SHELL {NONCE} {LEFT * RIGHT}", f"G4-SHELL {NONCE} {left * right}")
            self.assertEqual(self.validate(text, left=left, right=right), [])

    def test_unicode_separators_cannot_create_anchored_serial_frames(self):
        for separator in ("\x85", "\u2028", "\u2029"):
            with self.subTest(separator=repr(separator)):
                text = synthetic_transcript().replace("\nG4-BEGIN", separator + "G4-BEGIN")
                self.assertTrue(self.validate(text))

    def test_kernel_failure_before_or_after_result_invalidates_protocol(self):
        for failure in ("Kernel panic - not syncing", "Oops: 0000", "BUG: bad thing", "kernel BUG at file.c",
                        "Internal error: Oops",
                        "Unable to handle kernel paging request", "G4-ERROR bad challenge"):
            for text in (failure + "\n" + synthetic_transcript(), synthetic_transcript() + "\n" + failure):
                with self.subTest(failure=failure):
                    self.assertTrue(self.validate(text))

    def test_debug_messages_do_not_masquerade_as_bug_diagnostics(self):
        self.assertEqual(self.validate("[0.0] DEBUG: example diagnostic\n" + synthetic_transcript()), [])

    def test_corruption_oversize_and_truncated_lines_fail(self):
        for value in (None, [], 1, "\ud800", "\x00", "\x1b[31m", "\x7f", "\r"):
            with self.subTest(value=repr(value)):
                text = synthetic_transcript() + value if isinstance(value, str) else value
                self.assertTrue(self.validate(text))
        self.assertTrue(self.validate("x" * (witness.MAX_BYTES + 1)))
        end = synthetic_transcript().index(f"G4-SHELL {NONCE} {LEFT * RIGHT}") + len(f"G4-SHELL {NONCE} {LEFT * RIGHT}")
        self.assertTrue(self.validate(synthetic_transcript()[:end]))


class G4WitnessCommandTests(unittest.TestCase):
    def run_checker(self, path, *extra):
        return subprocess.run([sys.executable, str(ROOT / "tools/check_g4_transcript.py"), str(path),
                               "--nonce", NONCE, "--left", str(LEFT), "--right", str(RIGHT), *extra],
                              capture_output=True, text=True, cwd=path.parent, timeout=10)

    def test_cli_valid_invalid_and_absent_inputs_are_honest_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "serial.txt"
            result = self.run_checker(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("cannot read", result.stdout)
            for data in (b"\xff", b"BusyBox\n# ", synthetic_transcript().encode()):
                path.write_bytes(data)
                result = self.run_checker(path)
                valid = data == synthetic_transcript().encode()
                self.assertEqual(result.returncode, 0 if valid else 1, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)
                if valid:
                    self.assertIn("protocol ONLY", result.stdout)
                    self.assertIn("does not authenticate evidence or certify G4", result.stdout)
            for option, value in (("--left", "0"), ("--right", "1000000"), ("--nonce", "BAD"),
                                  ("--left", "not-an-int")):
                result = self.run_checker(path, option, value)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_cli_read_is_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "oversize.txt"
            with path.open("wb") as stream:
                stream.truncate(witness.MAX_BYTES + 1)
            result = self.run_checker(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("exceeds 8 MiB", result.stdout)

    def test_guest_script_shell_syntax_and_bad_arguments(self):
        script = ROOT / "experiments/linux-boot-witness/probe.sh"
        result = subprocess.run(["sh", "-n", str(script)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for args in ([], ["short"], ["G" * 32], [NONCE, "extra"]):
            result = subprocess.run(["sh", str(script), *args], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("G4-ERROR", result.stderr)
            self.assertNotIn("G4-BEGIN", result.stdout)

    def test_terminal_cleanup_failure_is_an_explicit_protocol_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            terminal = directory / "tty"
            terminal.write_text("#!/bin/sh\nprintf '/dev/ttySAC0\\n'\n", encoding="utf-8")
            terminal.chmod(0o755)
            settings = directory / "stty"
            settings.write_text("#!/bin/sh\nif [ \"$1\" = -g ]; then printf 'saved-state\\n'; else exit 1; fi\n",
                                encoding="utf-8")
            settings.chmod(0o755)
            environment = dict(os.environ, PATH=str(directory) + os.pathsep + os.environ.get("PATH", ""))
            result = subprocess.run(["sh", str(ROOT / "experiments/linux-boot-witness/probe.sh"), NONCE],
                                    env=environment, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("G4-ERROR terminal restoration failed", result.stderr)
            self.assertNotIn("G4-END", result.stdout)


class G4SerialBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "sys"
        self.physical = self.root / "devices/platform/soc/235200000.serial"
        self.driver = self.root / "bus/platform/drivers/samsung-uart"
        self.platform_link = self.root / "bus/platform/devices/235200000.serial"
        self.tty_link = self.root / "class/tty/ttySAC0/device"
        self.node = self.root / "firmware/devicetree/base/soc/serial@235200000"
        for path in (self.physical, self.driver, self.platform_link.parent, self.tty_link.parent, self.node):
            path.mkdir(parents=True, exist_ok=True)
        self.platform_link.symlink_to(self.physical)
        self.tty_link.symlink_to(self.physical)
        (self.physical / "driver").symlink_to(self.driver)
        (self.physical / "of_node").symlink_to(self.node)
        (self.node / "compatible").write_bytes(b"apple,s5l-uart\0")

    def run_binding(self):
        return subprocess.run(["sh", str(ROOT / "experiments/linux-boot-witness/serial-binding.sh"), str(self.root)],
                              capture_output=True, text=True, timeout=10)

    def assert_binding_failure(self):
        result = self.run_binding()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("G4-ERROR serial binding", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_direct_parent_binding_passes(self):
        result = self.run_binding()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "samsung-uart\n")

    def test_serial_core_nested_port_binding_passes(self):
        port = self.physical / "235200000.serial:0/235200000.serial:0.0"
        port.mkdir(parents=True)
        port_driver = self.root / "bus/serial-base/drivers/port"
        port_driver.mkdir(parents=True)
        (port / "driver").symlink_to(port_driver)
        self.tty_link.unlink()
        self.tty_link.symlink_to(port)
        result = self.run_binding()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "samsung-uart\n")

    def test_unrelated_sibling_with_shared_prefix_is_rejected(self):
        sibling = self.physical.with_name("235200000.serial-unrelated")
        sibling.mkdir()
        self.tty_link.unlink()
        self.tty_link.symlink_to(sibling)
        self.assert_binding_failure()

    def test_missing_and_dangling_device_symlinks_are_rejected(self):
        for link in (self.platform_link, self.tty_link, self.physical / "driver"):
            target = link.readlink()
            with self.subTest(link=str(link)):
                link.unlink()
                self.assert_binding_failure()
                link.symlink_to(self.root / "missing-device")
                self.assert_binding_failure()
                link.unlink()
                link.symlink_to(target)

    def test_physical_uart_must_resolve_under_devices(self):
        outside = self.root / "devices-unrelated/235200000.serial"
        outside.mkdir(parents=True)
        self.platform_link.unlink()
        self.platform_link.symlink_to(outside)
        self.tty_link.unlink()
        self.tty_link.symlink_to(outside)
        self.assert_binding_failure()

    def test_wrong_platform_driver_is_rejected(self):
        incorrect = self.driver.with_name("uart-pl011")
        incorrect.mkdir()
        (self.physical / "driver").unlink()
        (self.physical / "driver").symlink_to(incorrect)
        self.assert_binding_failure()

    def test_compatible_membership_is_exact_and_required(self):
        path = self.node / "compatible"
        for content in (b"arm,pl011\0", b"apple,s5l-uart-extra\0", b"prefix-apple,s5l-uart\0", b""):
            with self.subTest(content=content):
                path.write_bytes(content)
                self.assert_binding_failure()
        path.unlink()
        self.assert_binding_failure()
        path.write_bytes(b"other,compatible\0apple,s5l-uart\0")
        result = self.run_binding()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_helper_syntax_and_bad_arguments(self):
        helper = ROOT / "experiments/linux-boot-witness/serial-binding.sh"
        result = subprocess.run(["sh", "-n", str(helper)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        for args in ([], [str(self.root), "extra"], [str(self.root / "missing")]):
            with self.subTest(args=args):
                result = subprocess.run(["sh", str(helper), *args], capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("G4-ERROR serial binding", result.stderr)


if __name__ == "__main__":
    unittest.main()
