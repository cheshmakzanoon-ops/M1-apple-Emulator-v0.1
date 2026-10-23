"""P003 policy regressions; none of these fixtures is runtime G4 evidence."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import validate_boot_milestone as milestone


class BootMilestonePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((milestone.ROOT / milestone.MANIFEST).read_text(encoding="utf-8"))

    def test_reference_contract_passes(self):
        self.assertEqual(milestone.validate(self.reference), [])

    def test_top_level_types_and_missing_fields_are_diagnostics(self):
        for raw in (None, [], 1, True, "G4"):
            with self.subTest(raw=raw):
                self.assertTrue(milestone.validate(raw))
        for field in self.reference:
            broken = copy.deepcopy(self.reference)
            del broken[field]
            with self.subTest(missing=field):
                self.assertTrue(milestone.validate(broken))

    def test_policy_cannot_record_runtime_success(self):
        for field in ("passed", "result", "status"):
            for section in (None, "target", "witness", "sources"):
                broken = copy.deepcopy(self.reference)
                (broken if section is None else broken[section])[field] = True
                with self.subTest(field=field, section=section):
                    self.assertTrue(milestone.validate(broken))
        for collection in ("prerequisites", "observations"):
            broken = copy.deepcopy(self.reference)
            broken[collection][0]["passed"] = True
            self.assertTrue(milestone.validate(broken))

    def test_no_generic_platform_or_fidelity_promotion(self):
        cases = (("machine", "virt"), ("machine", "vmapple"), ("accelerator", "kvm"),
                 ("console", "ttyAMA0"), ("serial_driver", "uart-pl011"),
                 ("boot_mode", "stock-apple-firmware"), ("board", "J293"),
                 ("root_filesystem", "host filesystem"))
        for field, value in cases:
            broken = copy.deepcopy(self.reference)
            broken["target"][field] = value
            with self.subTest(field=field, value=value):
                self.assertTrue(milestone.validate(broken))
        for value in (["toolchain"], ["machine-macos"], ["machine-linux", "machine-macos"]):
            broken = copy.deepcopy(self.reference)
            broken["fidelity"] = value
            self.assertTrue(milestone.validate(broken))

    def test_every_prerequisite_and_observation_is_required_exactly_once(self):
        for field in ("prerequisites", "observations"):
            for index in range(len(self.reference[field])):
                for operation in ("missing", "duplicate", "unknown", "unhashable"):
                    broken = copy.deepcopy(self.reference)
                    if operation == "missing":
                        broken[field].pop(index)
                    elif operation == "duplicate":
                        broken[field].append(copy.deepcopy(broken[field][index]))
                    else:
                        broken[field][index]["id"] = "unknown" if operation == "unknown" else []
                    with self.subTest(field=field, index=index, operation=operation):
                        self.assertTrue(milestone.validate(broken))

    def test_malformed_collection_entries_and_invisible_prose_are_rejected(self):
        for field, text_field in (("prerequisites", "evidence"), ("observations", "requirement")):
            for value in (None, {}, "", True, [None], [[]]):
                broken = copy.deepcopy(self.reference)
                broken[field] = value
                with self.subTest(field=field, value=value):
                    self.assertTrue(milestone.validate(broken))
            for index in range(len(self.reference[field])):
                for value in (None, [], {}, "", " ", "hidden\nline", "two|cells", "<!-- hidden -->"):
                    broken = copy.deepcopy(self.reference)
                    broken[field][index][text_field] = value
                    with self.subTest(field=field, index=index, value=value):
                        self.assertTrue(milestone.validate(broken))

    def test_g3_and_future_integration_cannot_be_waived_or_renumbered(self):
        for index in range(len(self.reference["prerequisites"])):
            broken = copy.deepcopy(self.reference)
            broken["prerequisites"][index]["phases"] = ["P003"]
            self.assertTrue(milestone.validate(broken))
        broken = copy.deepcopy(self.reference)
        broken["prerequisites"] = [item for item in broken["prerequisites"] if item["id"] != "G3"]
        self.assertTrue(milestone.validate(broken))

    def test_every_frozen_numeric_limit_rejects_type_confusion_and_weakening(self):
        for section in (None, "witness"):
            source = self.reference if section is None else self.reference[section]
            for field, original in source.items():
                if type(original) is not int:
                    continue
                for value in (True, False, float(original), str(original), 0, -1, original + 1, None):
                    broken = copy.deepcopy(self.reference)
                    (broken if section is None else broken[section])[field] = value
                    with self.subTest(section=section, field=field, value=value):
                        self.assertTrue(milestone.validate(broken))

    def test_each_input_hash_record_field_artifact_and_substitute_is_mandatory(self):
        for record, fields in self.reference["evidence_fields"].items():
            for index in range(len(fields)):
                broken = copy.deepcopy(self.reference)
                broken["evidence_fields"][record].pop(index)
                with self.subTest(record=record, missing=fields[index]):
                    self.assertTrue(milestone.validate(broken))
        for field in ("required_artifacts", "excluded_substitutes"):
            for index in range(len(self.reference[field])):
                broken = copy.deepcopy(self.reference)
                broken[field].pop(index)
                with self.subTest(field=field, index=index):
                    self.assertTrue(milestone.validate(broken))

    def test_irq_timer_and_post_probe_shell_requirements_are_independent(self):
        for field, value in (("uart_irq_chip", "AIC-FIQ"), ("timer_irq_chip", "AIC"),
                             ("uart_irq_action", "ttySAC0"), ("timer_irq_action", "virtio0"),
                             ("shell_followup", "none")):
            broken = copy.deepcopy(self.reference)
            broken["witness"][field] = value
            self.assertTrue(milestone.validate(broken))

    def test_source_pins_cannot_drift_to_latest_or_unrelated_pages(self):
        for identifier in self.reference["sources"]:
            for value in (None, "http://example.org", "https://example.org", "https://github.com/torvalds/linux/blob/master/README"):
                broken = copy.deepcopy(self.reference)
                broken["sources"][identifier] = value
                with self.subTest(identifier=identifier, value=value):
                    self.assertTrue(milestone.validate(broken))


class BootMilestoneRepositoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.paths = (milestone.MANIFEST, milestone.SPECIFICATION, milestone.REFERENCES,
                      Path(milestone.WITNESS["guest_script"]), Path(milestone.WITNESS["binding_helper"]),
                      Path(milestone.WITNESS["checker"]))
        for relative in self.paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((milestone.ROOT / relative).read_bytes())

    def assert_invalid(self, relative):
        errors = milestone.validate_repository(self.root)
        self.assertTrue(any(str(relative) in error for error in errors), errors)

    def test_repository_and_crlf_snapshot_pass(self):
        self.assertEqual(milestone.validate_repository(), [])
        self.assertEqual(milestone.validate_repository(self.root), [])
        for relative in self.paths:
            path = self.root / relative
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertEqual(milestone.validate_repository(self.root), [])

    def test_each_witness_dependency_must_exist_be_nonempty_and_utf8(self):
        for relative in self.paths:
            path = self.root / relative
            original = path.read_bytes()
            path.unlink()
            self.assert_invalid(relative)
            path.write_bytes(b"\xff")
            self.assert_invalid(relative)
            path.write_bytes(b"")
            self.assert_invalid(relative)
            path.write_bytes(original)

    def test_malformed_json_and_duplicate_keys_fail_without_hiding_values(self):
        path = self.root / milestone.MANIFEST
        original = path.read_text(encoding="utf-8")
        for text in ("{broken", "[]", "null", "true",
                     original.replace('"gate": "G4"', '"gate": "G0", "gate": "G4"'),
                     original.replace('"cold_boots": 3', '"cold_boots": 0, "cold_boots": 3')):
            with self.subTest(text=text[:80]):
                path.write_text(text, encoding="utf-8")
                self.assert_invalid(milestone.MANIFEST)

    def test_contract_cannot_be_changed_duplicated_or_hidden_in_publication(self):
        path = self.root / milestone.SPECIFICATION
        original = path.read_text(encoding="utf-8")
        raw = json.loads((self.root / milestone.MANIFEST).read_text(encoding="utf-8"))
        block = milestone.render_contract(raw)
        for replacement in ("", block + "\n\n" + block, block.replace("| G3 |", "| optional |"),
                            "<!--\n" + block + "\n-->", "```\n" + block + "\n```",
                            "~~~text\n" + block + "\n~~~"):
            with self.subTest(replacement=replacement[:40]):
                path.write_text(original.replace(block, replacement), encoding="utf-8")
                self.assert_invalid(milestone.SPECIFICATION)

    def test_each_visible_source_link_is_required(self):
        path = self.root / milestone.REFERENCES
        original = path.read_text(encoding="utf-8")
        for identifier, url in milestone.SOURCES.items():
            with self.subTest(identifier=identifier):
                path.write_text(original.replace(f"]({url})", "](https://example.org)"), encoding="utf-8")
                self.assert_invalid(milestone.REFERENCES)

    def test_coordinated_generic_machine_relabeling_cannot_redefine_g4(self):
        manifest = self.root / milestone.MANIFEST
        spec = self.root / milestone.SPECIFICATION
        manifest.write_text(manifest.read_text(encoding="utf-8").replace("apple-m1-lab", "virt"), encoding="utf-8")
        spec.write_text(spec.read_text(encoding="utf-8").replace("apple-m1-lab", "virt"), encoding="utf-8")
        self.assert_invalid(milestone.MANIFEST)

    def test_cli_root_resolution_success_and_failure_are_honest(self):
        command = [sys.executable, str(milestone.ROOT / "tools/validate_boot_milestone.py")]
        for options in ([], ["--root", str(self.root)]):
            result = subprocess.run(command + options, cwd=self.root, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Valid P003 contract", result.stdout)
            self.assertIn("does not establish a passed G4", result.stdout)
        (self.root / milestone.MANIFEST).write_text("{broken", encoding="utf-8")
        result = subprocess.run(command + ["--root", str(self.root)], cwd=self.root,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(str(milestone.MANIFEST), result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
