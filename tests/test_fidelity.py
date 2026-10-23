"""Regression evidence for P002 scope separation and published gate fidelity."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import validate_fidelity as fidelity


class FidelityMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((fidelity.ROOT / fidelity.MANIFEST).read_text(encoding="utf-8"))

    def test_published_policy_passes(self):
        self.assertEqual(fidelity.validate(self.reference), [])

    def test_invalid_top_level_and_schema_versions_are_diagnostics(self):
        for value in (None, [], "policy", 1, True):
            with self.subTest(value=value):
                self.assertTrue(fidelity.validate(value))
        for value in (None, False, True, 1.0, "1", 2, [], {}):
            with self.subTest(version=value):
                broken = copy.deepcopy(self.reference)
                broken["schema_version"] = value
                self.assertTrue(fidelity.validate(broken))

    def test_missing_and_extra_top_level_fields_rejected(self):
        for field in self.reference:
            with self.subTest(missing=field):
                broken = copy.deepcopy(self.reference)
                del broken[field]
                self.assertTrue(fidelity.validate(broken))
        broken = copy.deepcopy(self.reference)
        broken["passed"] = True
        self.assertTrue(fidelity.validate(broken))

    def test_every_level_and_gate_is_required_exactly_once(self):
        for field in ("levels", "gates"):
            for index, entry in enumerate(self.reference[field]):
                for operation in ("missing", "duplicate", "unknown", "unhashable"):
                    with self.subTest(field=field, identifier=entry["id"], operation=operation):
                        broken = copy.deepcopy(self.reference)
                        if operation == "missing":
                            broken[field].pop(index)
                        elif operation == "duplicate":
                            broken[field].append(copy.deepcopy(entry))
                        else:
                            broken[field][index]["id"] = "unknown" if operation == "unknown" else []
                        self.assertTrue(fidelity.validate(broken))

    def test_malformed_collection_and_entry_types_rejected(self):
        for field in ("levels", "gates"):
            for value in (None, {}, "entry", 2, True):
                with self.subTest(field=field, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken[field] = value
                    self.assertTrue(fidelity.validate(broken))
                    broken[field] = [value]
                    self.assertTrue(fidelity.validate(broken))

    def test_each_definition_field_requires_nonempty_plain_line(self):
        for index, entry in enumerate(self.reference["levels"]):
            for field in entry:
                for value in (None, [], {}, True, "", "  ", "text\ntext", "text|text"):
                    with self.subTest(identifier=entry["id"], field=field, value=value):
                        broken = copy.deepcopy(self.reference)
                        broken["levels"][index][field] = value
                        self.assertTrue(fidelity.validate(broken))
                with self.subTest(identifier=entry["id"], missing=field):
                    broken = copy.deepcopy(self.reference)
                    del broken["levels"][index][field]
                    self.assertTrue(fidelity.validate(broken))

    def test_titles_cannot_relabel_an_independent_dimension(self):
        for index, entry in enumerate(self.reference["levels"]):
            with self.subTest(identifier=entry["id"]):
                broken = copy.deepcopy(self.reference)
                broken["levels"][index]["title"] = "Complete M1 compatibility"
                self.assertTrue(fidelity.validate(broken))

    def test_every_gate_retains_its_bounded_fidelity_mapping(self):
        for index, entry in enumerate(self.reference["gates"]):
            for value in (None, {}, "isa", [], ["unknown"], ["machine-macos"],
                          entry["levels"] + [entry["levels"][0]], [[]]):
                with self.subTest(identifier=entry["id"], levels=value):
                    broken = copy.deepcopy(self.reference)
                    broken["gates"][index]["levels"] = value
                    self.assertTrue(fidelity.validate(broken))

    def test_development_and_formal_release_kinds_cannot_be_swapped(self):
        for index, entry in enumerate(self.reference["gates"]):
            with self.subTest(identifier=entry["id"]):
                broken = copy.deepcopy(self.reference)
                broken["gates"][index]["kind"] = "release" if entry["kind"] == "development" else "development"
                self.assertTrue(fidelity.validate(broken))

    def test_g1_elf_execution_cannot_certify_a_peripheral(self):
        broken = copy.deepcopy(self.reference)
        gate = next(gate for gate in broken["gates"] if gate["id"] == "G1")
        gate["levels"] = ["isa", "apple-cpu", "peripheral"]
        self.assertTrue(any("G1.levels" in error for error in fidelity.validate(broken)))

    def test_gate_observables_and_boundaries_must_be_published(self):
        for index, entry in enumerate(self.reference["gates"]):
            for field in ("test", "scope"):
                for value in (None, [], {}, "", "  ", "a\nb", "a|b"):
                    with self.subTest(identifier=entry["id"], field=field, value=value):
                        broken = copy.deepcopy(self.reference)
                        broken["gates"][index][field] = value
                        self.assertTrue(fidelity.validate(broken))
            for field in entry:
                with self.subTest(identifier=entry["id"], missing=field):
                    broken = copy.deepcopy(self.reference)
                    del broken["gates"][index][field]
                    self.assertTrue(fidelity.validate(broken))

    def test_policy_entries_cannot_carry_runtime_success_status(self):
        for collection in ("levels", "gates"):
            for index, entry in enumerate(self.reference[collection]):
                with self.subTest(collection=collection, identifier=entry["id"]):
                    broken = copy.deepcopy(self.reference)
                    broken[collection][index]["passed"] = True
                    self.assertTrue(fidelity.validate(broken))


class FidelityRepositoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in (fidelity.MANIFEST, fidelity.ARCHITECTURE, fidelity.ROADMAP):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((fidelity.ROOT / relative).read_bytes())
        self.reference = json.loads((self.root / fidelity.MANIFEST).read_text(encoding="utf-8"))
        self.architecture = self.root / fidelity.ARCHITECTURE
        self.roadmap = self.root / fidelity.ROADMAP

    def assert_invalid(self, path):
        errors = fidelity.validate_repository(self.root)
        self.assertTrue(any(str(path) in error for error in errors), errors)

    def test_repository_and_copied_snapshot_pass(self):
        self.assertEqual(fidelity.validate_repository(), [])
        self.assertEqual(fidelity.validate_repository(self.root), [])

    def test_each_definition_cannot_be_removed_duplicated_or_rewritten(self):
        original = self.architecture.read_text(encoding="utf-8")
        for entry in self.reference["levels"]:
            block = fidelity.render_levels({"levels": [entry]})
            for operation, replacement in enumerate(("", block + "\n\n" + block,
                                                     block.replace(entry["definition"], "Complete M1 emulation."))):
                with self.subTest(identifier=entry["id"], operation=operation):
                    self.architecture.write_text(original.replace(block, replacement), encoding="utf-8")
                    self.assert_invalid(fidelity.ARCHITECTURE)

    def test_each_gate_cannot_be_removed_duplicated_or_reclassified(self):
        original = self.architecture.read_text(encoding="utf-8")
        for gate in self.reference["gates"]:
            row = next(line for line in original.splitlines() if line.startswith(f"| {gate['id']} |"))
            for operation, replacement in enumerate(("", row + "\n" + row,
                                                     row.replace(f"`{gate['levels'][0]}`", "`machine-macos`"))):
                with self.subTest(identifier=gate["id"], operation=operation):
                    self.architecture.write_text(original.replace(row, replacement), encoding="utf-8")
                    self.assert_invalid(fidelity.ARCHITECTURE)

    def test_definitions_and_tables_hidden_in_code_or_comments_do_not_count(self):
        original = self.architecture.read_text(encoding="utf-8")
        for block in (fidelity.render_levels(self.reference),
                      fidelity.render_gates(self.reference, "development"),
                      fidelity.render_gates(self.reference, "release")):
            for before, after in (("```text\n", "\n```"), ("~~~\n", "\n~~~"),
                                  ("<!--\n", "\n-->"), ("````\n```\n", "\n````")):
                with self.subTest(block=block.splitlines()[0], before=before):
                    self.architecture.write_text(original.replace(block, before + block + after), encoding="utf-8")
                    self.assert_invalid(fidelity.ARCHITECTURE)

    def test_additional_unknown_gate_and_definition_are_rejected(self):
        original = self.architecture.read_text(encoding="utf-8")
        for addition in ("\n| G7 | unknown | `machine-macos` | unproven |\n",
                         "\n### `complete-m1` — Full compatibility\n"):
            with self.subTest(addition=addition):
                self.architecture.write_text(original + addition, encoding="utf-8")
                self.assert_invalid(fidelity.ARCHITECTURE)

    def test_every_formal_phase_requires_one_matching_visible_annotation(self):
        original = self.roadmap.read_text(encoding="utf-8")
        for identifier in ("P361", "P362", "P363", "P364", "P365"):
            row = next(line for line in original.splitlines()
                       if line.startswith("- [") and f"**{identifier} —" in line)
            for operation, replacement in enumerate(("", row + "\n" + row, row.replace("**Fidelity:**", "**Other:**"),
                                                     row.replace("**Fidelity:**", "**Fidelity:** `machine-macos`,"),
                                                     "<!--\n" + row + "\n-->", "```\n" + row + "\n```")):
                with self.subTest(identifier=identifier, operation=operation):
                    self.roadmap.write_text(original.replace(row, replacement), encoding="utf-8")
                    self.assert_invalid(fidelity.ROADMAP)

    def test_classification_does_not_freeze_future_phase_completion_status(self):
        original = self.roadmap.read_text(encoding="utf-8")
        self.roadmap.write_text(original.replace("- [ ] **P361", "- [x] **P361"), encoding="utf-8")
        self.assertEqual(fidelity.validate_repository(self.root), [])

    def test_coordinated_generic_smoke_promotion_is_rejected(self):
        broken = copy.deepcopy(self.reference)
        gate = next(gate for gate in broken["gates"] if gate["id"] == "G0")
        gate["levels"] = ["machine-linux"]
        (self.root / fidelity.MANIFEST).write_text(json.dumps(broken), encoding="utf-8")
        original = self.architecture.read_text(encoding="utf-8")
        self.architecture.write_text(original.replace(fidelity.render_gates(self.reference, "development"),
                                                      fidelity.render_gates(broken, "development")), encoding="utf-8")
        self.assert_invalid(fidelity.MANIFEST)

    def test_missing_non_utf8_and_invalid_json_are_diagnostics(self):
        for relative in (fidelity.MANIFEST, fidelity.ARCHITECTURE, fidelity.ROADMAP):
            path = self.root / relative
            original = path.read_bytes()
            path.unlink()
            self.assert_invalid(relative)
            path.write_bytes(b"\xff")
            self.assert_invalid(relative)
            path.write_bytes(original)
        for value in ("{invalid", "[]", "null", "true"):
            with self.subTest(value=value):
                (self.root / fidelity.MANIFEST).write_text(value, encoding="utf-8")
                self.assert_invalid(fidelity.MANIFEST)

    def test_crlf_snapshots_are_supported(self):
        for relative in (fidelity.MANIFEST, fidelity.ARCHITECTURE, fidelity.ROADMAP):
            path = self.root / relative
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertEqual(fidelity.validate_repository(self.root), [])

    def test_duplicate_json_keys_cannot_hide_conflicting_policy_values(self):
        original = json.dumps(self.reference)
        for content in (original.replace('"schema_version": 1', '"schema_version": 2, "schema_version": 1'),
                        original.replace('"id": "G0"', '"id": "unknown", "id": "G0"')):
            with self.subTest(content=content[:100]):
                (self.root / fidelity.MANIFEST).write_text(content, encoding="utf-8")
                errors = fidelity.validate_repository(self.root)
                self.assertTrue(any("duplicate JSON key" in error for error in errors), errors)

    def test_cli_default_root_and_alternate_root_are_cwd_independent(self):
        command = [sys.executable, str(fidelity.ROOT / "tools/validate_fidelity.py")]
        for arguments in ([], ["--root", str(self.root)]):
            with self.subTest(arguments=arguments):
                result = subprocess.run(command + arguments, cwd=self.root, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("Valid P002 fidelity policy", result.stdout)
                self.assertIn("does not establish passed runtime gates", result.stdout)
        for value in ("{broken", "[]"):
            with self.subTest(value=value):
                (self.root / fidelity.MANIFEST).write_text(value, encoding="utf-8")
                result = subprocess.run(command + ["--root", str(self.root)], cwd=self.root,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(str(fidelity.MANIFEST), result.stdout)
                self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
