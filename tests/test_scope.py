"""P004 regressions: scope exclusions must survive misleading milestone edits."""

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import validate_fidelity as fidelity
from tools import validate_scope as scope


class ScopeMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((scope.ROOT / scope.MANIFEST).read_text(encoding="utf-8"))

    def test_published_contract_passes(self):
        self.assertEqual(scope.validate(self.reference), [])

    def test_schema_release_and_success_gate_are_fixed(self):
        for value in (None, [], "scope", 1, True):
            with self.subTest(value=value):
                self.assertTrue(scope.validate(value))
        for field, values in (
            ("schema_version", (None, True, 1.0, "1", 2)),
            ("release", (None, "v0.2", "v1.0", [])),
            ("success_gate", (None, "G0", "P365", {})),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken[field] = value
                    self.assertTrue(scope.validate(broken))

    def test_capabilities_cannot_be_required_or_implemented(self):
        for index, capability in enumerate(self.reference["capabilities"]):
            for field in ("required_for_v0_1", "implemented"):
                for value in (True, 0, 1, "false", None, [], {}):
                    with self.subTest(capability=capability["id"], field=field, value=value):
                        broken = copy.deepcopy(self.reference)
                        broken["capabilities"][index][field] = value
                        self.assertTrue(scope.validate(broken))

    def test_missing_and_extra_fields_cannot_hide_runtime_claims(self):
        for field in self.reference:
            with self.subTest(missing=field):
                broken = copy.deepcopy(self.reference)
                del broken[field]
                self.assertTrue(scope.validate(broken))
        for index, capability in enumerate(self.reference["capabilities"]):
            with self.subTest(capability=capability["id"]):
                broken = copy.deepcopy(self.reference)
                broken["capabilities"][index]["shipped"] = True
                self.assertTrue(scope.validate(broken))
                broken = copy.deepcopy(self.reference)
                del broken["capabilities"][index]["boundary"]
                self.assertTrue(scope.validate(broken))

    def test_each_capability_is_required_exactly_once(self):
        for index, capability in enumerate(self.reference["capabilities"]):
            for operation in ("missing", "duplicate", "unknown", "unhashable"):
                with self.subTest(capability=capability["id"], operation=operation):
                    broken = copy.deepcopy(self.reference)
                    if operation == "missing":
                        broken["capabilities"].pop(index)
                    elif operation == "duplicate":
                        broken["capabilities"].append(copy.deepcopy(capability))
                    else:
                        broken["capabilities"][index]["id"] = (
                            "native-speed" if operation == "unknown" else []
                        )
                    self.assertTrue(scope.validate(broken))

    def test_malformed_collections_and_prose_are_diagnostics(self):
        for field in ("capabilities", "gate_exclusions", "sources"):
            for value in (None, "", 7, True):
                with self.subTest(field=field, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken[field] = value
                    self.assertTrue(scope.validate(broken))
        for value in (None, [], "record", 3, True):
            with self.subTest(entry=value):
                broken = copy.deepcopy(self.reference)
                broken["capabilities"] = [value]
                self.assertTrue(scope.validate(broken))
        for index, capability in enumerate(self.reference["capabilities"]):
            for field in ("boundary", "allowed_research", "promotion_evidence"):
                for value in ("", "   ", None, [], {}):
                    with self.subTest(capability=capability["id"], field=field, value=value):
                        broken = copy.deepcopy(self.reference)
                        broken["capabilities"][index][field] = value
                        self.assertTrue(scope.validate(broken))

    def test_research_phase_ranges_and_source_membership_are_exact(self):
        for index, capability in enumerate(self.reference["capabilities"]):
            for field in ("related_phases", "sources"):
                for operation in ("missing", "duplicate", "unknown", "malformed"):
                    with self.subTest(capability=capability["id"], field=field, operation=operation):
                        broken = copy.deepcopy(self.reference)
                        values = broken["capabilities"][index][field]
                        if operation == "missing":
                            values.pop()
                        elif operation == "duplicate":
                            values.append(values[0])
                        elif operation == "unknown":
                            values[0] = "G4" if field == "related_phases" else "unreviewed"
                        else:
                            values[0] = []
                        self.assertTrue(scope.validate(broken))

    def test_every_gate_excludes_all_three_capabilities(self):
        for gate in self.reference["gate_exclusions"]:
            for operation in ("missing", "omission", "duplicate", "unknown", "malformed"):
                with self.subTest(gate=gate, operation=operation):
                    broken = copy.deepcopy(self.reference)
                    if operation == "missing":
                        del broken["gate_exclusions"][gate]
                    elif operation == "omission":
                        broken["gate_exclusions"][gate].pop()
                    elif operation == "duplicate":
                        broken["gate_exclusions"][gate].append(
                            broken["gate_exclusions"][gate][0]
                        )
                    elif operation == "unknown":
                        broken["gate_exclusions"][gate][0] = "native-speed"
                    else:
                        broken["gate_exclusions"][gate] = {}
                    self.assertTrue(scope.validate(broken))
        broken = copy.deepcopy(self.reference)
        broken["gate_exclusions"]["G7"] = list(broken["gate_exclusions"]["G4"])
        self.assertTrue(scope.validate(broken))

    def test_reviewed_sources_cannot_be_removed_or_redirected(self):
        for source in self.reference["sources"]:
            for operation in ("missing", "redirect", "malformed"):
                with self.subTest(source=source, operation=operation):
                    broken = copy.deepcopy(self.reference)
                    if operation == "missing":
                        del broken["sources"][source]
                    elif operation == "redirect":
                        broken["sources"][source] = "https://example.invalid/unsupported"
                    else:
                        broken["sources"][source] = {}
                    self.assertTrue(scope.validate(broken))


class ScopeClaimTests(unittest.TestCase):
    def test_known_affirmative_shipping_and_requirement_claims_are_rejected(self):
        for claim in (
            "v0.1 ships fully functioning AGX graphics.",
            "Cycle accuracy is implemented.",
            "G4 certifies unmodified macOS.",
            "v0.1 ships GPU graphics.",
            "GPU graphics are required for v0.1.",
            "Cycle-accurate execution ships in v0.1.",
            "v0.1 ships **GPU graphics**.",
            "v0.1 ships fully functioning\nAGX graphics.",
            "G4 will require unmodified macOS.",
            "GPU graphics is implemented without Apple firmware.",
            "v0.1 ships GPU graphics, not cycle accuracy.",
            "AGX no-op queue provides full GPU graphics.",
        ):
            with self.subTest(claim=claim):
                self.assertTrue(scope.audit_claims(claim, "fixture.md"))

    def test_a_negative_clause_cannot_excuse_a_later_positive_claim(self):
        for claim in (
            "No cycle accuracy; unmodified macOS ships.",
            "Cycle accuracy is not implemented. Unmodified macOS ships.",
            "v0.1 does not provide cycle accuracy; it ships unmodified macOS.",
            "No GPU graphics, but unmodified macOS ships.",
        ):
            with self.subTest(claim=claim):
                self.assertTrue(scope.audit_claims(claim, "fixture.md"))

    def test_explicit_exclusions_and_bounded_research_remain_valid(self):
        for statement in (
            "Cycle accuracy is not implemented.",
            "Unmodified macOS is not required for v0.1.",
            "Research a shader interpreter without claiming full AGX graphics.",
            "v0.1 does not ship GPU graphics.",
            "G4 does not establish macOS compatibility.",
            "An independent framebuffer experiment does not establish AGX graphics.",
            "GPU graphics remain an exploratory non-goal.",
            "Cycle messages across a subset of cores.",
            "Neither cycle accuracy nor GPU graphics is implemented.",
            "Skeletal AGX MMIO is implemented.",
            "An AGX no-op queue is implemented.",
            "The AGX shader decoder is implemented.",
        ):
            with self.subTest(statement=statement):
                self.assertEqual(scope.audit_claims(statement, "fixture.md"), [])

    def test_optional_research_cannot_become_a_release_dependency(self):
        for claim in (
            "WS20 is required for v0.1.",
            "G4 depends on P286-P300.",
            "P365 requires P315.",
        ):
            with self.subTest(claim=claim):
                self.assertTrue(scope.audit_claims(claim, "fixture.md"))
        for statement in ("WS20 requires G4.", "G4 is not blocked by WS21."):
            with self.subTest(statement=statement):
                self.assertEqual(scope.audit_claims(statement, "fixture.md"), [])


class ScopeRepositoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "snapshot"
        shutil.copytree(
            scope.ROOT,
            self.root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "build", "vendor", ".venv"),
        )
        self.reference = json.loads((self.root / scope.MANIFEST).read_text(encoding="utf-8"))

    def assert_invalid(self, path=None):
        errors = scope.validate_repository(self.root)
        self.assertTrue(errors)
        if path is not None:
            self.assertTrue(any(str(path) in error for error in errors), errors)

    def test_repository_and_fresh_snapshot_pass(self):
        self.assertEqual(scope.validate_repository(), [])
        self.assertEqual(scope.validate_repository(self.root), [])

    def test_each_publication_requires_one_visible_scope_declaration(self):
        fence = chr(96) * 3
        for relative in scope.PUBLICATIONS:
            path = self.root / relative
            original = path.read_text(encoding="utf-8")
            self.assertEqual(original.count(scope.DECLARATION), 1)
            for replacement in (
                "",
                scope.DECLARATION + "\n" + scope.DECLARATION,
                "<!--\n" + scope.DECLARATION + "\n-->",
                fence + "\n" + scope.DECLARATION + "\n" + fence,
                "~~~\n" + scope.DECLARATION + "\n~~~",
            ):
                with self.subTest(path=relative, replacement=replacement):
                    try:
                        path.write_text(
                            original.replace(scope.DECLARATION, replacement), encoding="utf-8"
                        )
                        self.assert_invalid(relative)
                    finally:
                        path.write_text(original, encoding="utf-8")

    def test_generated_contract_cannot_be_removed_duplicated_or_hidden(self):
        path = self.root / scope.SPECIFICATION
        original = path.read_text(encoding="utf-8")
        contract = scope.render_contract(self.reference)
        self.assertEqual(original.count(contract), 1)
        fence = chr(96) * 3
        for replacement in (
            "",
            contract + "\n\n" + contract,
            "<!--\n" + contract + "\n-->",
            fence + "\n" + contract + "\n" + fence,
        ):
            with self.subTest(replacement=replacement[:60]):
                try:
                    path.write_text(original.replace(contract, replacement), encoding="utf-8")
                    self.assert_invalid(scope.SPECIFICATION)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_all_optional_phases_need_the_visible_nonrequired_annotation(self):
        path = self.root / "ROADMAP_365_PHASES.md"
        original = path.read_text(encoding="utf-8")
        annotation = "**Scope:** exploratory; not required for v0.1."
        for number in range(286, 316):
            phase = f"P{number:03}"
            row = next(line for line in original.splitlines() if f"**{phase} —" in line)
            self.assertTrue(row.endswith(annotation), row)
            try:
                path.write_text(
                    original.replace(row, row.removesuffix(annotation)), encoding="utf-8"
                )
                self.assert_invalid("ROADMAP_365_PHASES.md")
            finally:
                path.write_text(original, encoding="utf-8")

    def test_proven_narrow_research_can_complete_without_awarding_full_capability(self):
        path = self.root / "ROADMAP_365_PHASES.md"
        text = path.read_text(encoding="utf-8")
        for phase in ("P290", "P293", "P296", "P315"):
            text = text.replace(f"- [ ] **{phase}", f"- [x] **{phase}")
        path.write_text(text, encoding="utf-8")
        self.assertEqual(scope.validate_repository(self.root), [])

    def test_coordinated_fidelity_and_document_promotion_is_rejected_for_every_gate(self):
        manifest_path = self.root / fidelity.MANIFEST
        architecture_path = self.root / fidelity.ARCHITECTURE
        original_json = manifest_path.read_text(encoding="utf-8")
        original_architecture = architecture_path.read_text(encoding="utf-8")
        reference = json.loads(original_json)
        for index, gate in enumerate(reference["gates"]):
            with self.subTest(gate=gate["id"]):
                broken = copy.deepcopy(reference)
                broken["gates"][index]["scope"] = (
                    "v0.1 ships cycle-accurate Firestorm execution, "
                    "fully functioning AGX graphics and unmodified macOS."
                )
                try:
                    manifest_path.write_text(json.dumps(broken), encoding="utf-8")
                    architecture_path.write_text(
                        original_architecture.replace(
                            fidelity.render_gates(reference, gate["kind"]),
                            fidelity.render_gates(broken, gate["kind"]),
                        ),
                        encoding="utf-8",
                    )
                    # Proves this mutation evades the older synchronization-only check.
                    self.assertEqual(fidelity.validate_repository(self.root), [])
                    self.assert_invalid()
                finally:
                    manifest_path.write_text(original_json, encoding="utf-8")
                    architecture_path.write_text(original_architecture, encoding="utf-8")

    def test_false_claims_in_new_release_notes_are_audited(self):
        path = self.root / "docs/release-notes.md"
        for statement in (
            "v0.1 ships GPU graphics.",
            "G4 certifies unmodified macOS.",
            "Cycle accuracy is implemented.",
        ):
            with self.subTest(statement=statement):
                path.write_text("# Release notes\n\n" + statement + "\n", encoding="utf-8")
                self.assert_invalid("release-notes.md")

    def test_coordinated_scope_boundary_promotion_is_rejected(self):
        path = self.root / scope.SPECIFICATION
        original = path.read_text(encoding="utf-8")
        broken = copy.deepcopy(self.reference)
        capability = next(entry for entry in broken["capabilities"]
                          if entry["id"] == "gpu-graphics")
        capability["boundary"] = "GPU graphics is implemented without Apple firmware."
        (self.root / scope.MANIFEST).write_text(json.dumps(broken), encoding="utf-8")
        path.write_text(
            original.replace(scope.render_contract(self.reference), scope.render_contract(broken)),
            encoding="utf-8",
        )
        self.assert_invalid(scope.MANIFEST)

    def test_deceptive_phase_result_is_rejected(self):
        path = self.root / "ROADMAP_365_PHASES.md"
        original = path.read_text(encoding="utf-8")
        row = next(line for line in original.splitlines() if "**P210 —" in line)
        path.write_text(
            original.replace(row, row + " **Result:** G4 certifies unmodified macOS."),
            encoding="utf-8",
        )
        self.assert_invalid("ROADMAP_365_PHASES.md")

    def test_missing_invalid_utf8_and_duplicate_key_inputs_are_diagnostics(self):
        for relative in (scope.MANIFEST, scope.SPECIFICATION):
            path = self.root / relative
            original = path.read_bytes()
            for operation in ("missing", "non-utf8"):
                with self.subTest(path=relative, operation=operation):
                    try:
                        if operation == "missing":
                            path.unlink()
                        else:
                            path.write_bytes(b"\xff\xfe")
                        self.assert_invalid(relative)
                    finally:
                        path.write_bytes(original)
        path = self.root / scope.MANIFEST
        original = path.read_text(encoding="utf-8")
        for text in (
            "{",
            "null",
            original.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'),
        ):
            with self.subTest(json=text[:70]):
                try:
                    path.write_text(text, encoding="utf-8")
                    self.assert_invalid(scope.MANIFEST)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_cli_foreign_working_directory_root_and_failure_exit_status(self):
        script = scope.ROOT / "tools/validate_scope.py"
        for extra in ([], ["--root", str(self.root)]):
            with self.subTest(arguments=extra):
                result = subprocess.run(
                    [sys.executable, str(script), *extra],
                    cwd=self.root.parent,
                    text=True,
                    capture_output=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
        (self.root / scope.MANIFEST).write_text("{", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(self.root)],
            cwd=self.root.parent,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scope.json", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()

