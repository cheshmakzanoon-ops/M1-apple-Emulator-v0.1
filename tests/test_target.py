"""Regression evidence for P001 identity drift and entrypoint consistency."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import validate_target as target


class TargetMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((target.ROOT / target.MAP_RELATIVE).read_text(encoding="utf-8"))

    def test_reference_target_passes(self):
        self.assertEqual(target.validate(self.reference), [])

    def test_each_identity_field_is_frozen(self):
        for section, fields in ((None, target.IDENTITY), ("target", target.TARGET_IDENTITY)):
            for field in fields:
                with self.subTest(section=section, field=field):
                    broken = copy.deepcopy(self.reference)
                    owner = broken if section is None else broken[section]
                    owner[field] = "another target"
                    self.assertTrue(any(field in error for error in target.validate(broken)))

    def test_compatible_order_is_significant(self):
        broken = copy.deepcopy(self.reference)
        broken["target"]["linux_compatible"].reverse()
        self.assertTrue(any("linux_compatible" in error for error in target.validate(broken)))

    def test_non_object_metadata_and_target_rejected(self):
        for value in (None, [], "T8103", 1, True):
            with self.subTest(value=value):
                self.assertTrue(target.validate(value))
                broken = copy.deepcopy(self.reference)
                broken["target"] = value
                self.assertTrue(target.validate(broken))

    def test_missing_or_malformed_fields_rejected(self):
        fields = set(target.TARGET_IDENTITY) | {
            "identity_sources", "excluded_soc_variants", "excluded_t8103_boards", "excluded_families",
        }
        for field in fields:
            for value in (None, [], {}):
                with self.subTest(field=field, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken["target"][field] = value
                    self.assertTrue(target.validate(broken))
            with self.subTest(missing=field):
                broken = copy.deepcopy(self.reference)
                del broken["target"][field]
                self.assertTrue(target.validate(broken))

    def test_required_sources_resolve_to_https(self):
        for key in target.IDENTITY_SOURCES:
            for value in (None, "http://example.com/source", "https://", "https://bad host/source", [],
                          "https://user:password@example.com/source", "https://[", "https://example.com:invalid"):
                with self.subTest(key=key, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken["sources"][key] = value
                    self.assertTrue(any(f"sources.{key}" in error for error in target.validate(broken)))
        for value in (None, [], {}):
            with self.subTest(sources=value):
                broken = copy.deepcopy(self.reference)
                broken["sources"] = value
                self.assertTrue(target.validate(broken))

    def test_membership_lists_reject_duplicates_and_unknowns(self):
        for field in ("identity_sources", "excluded_t8103_boards", "excluded_families"):
            for operation in ("duplicate", "unknown", "non-string"):
                with self.subTest(field=field, operation=operation):
                    broken = copy.deepcopy(self.reference)
                    values = broken["target"][field]
                    values[-1] = values[0] if operation == "duplicate" else "unknown" if operation == "unknown" else {}
                    self.assertTrue(any(field in error for error in target.validate(broken)))

    def test_exclusions_cannot_include_target_or_mislabel_variants(self):
        for field, key, value in (
            ("excluded_soc_variants", "T8103", "Apple M1"),
            ("excluded_soc_variants", "T6000", "Apple M1 Max"),
        ):
            with self.subTest(field=field, key=key):
                broken = copy.deepcopy(self.reference)
                broken["target"][field][key] = value
                self.assertTrue(target.validate(broken))
        broken = copy.deepcopy(self.reference)
        broken["target"]["excluded_t8103_boards"].append("J274")
        self.assertTrue(any("J274 must not be excluded" in error for error in target.validate(broken)))

    def test_source_and_exclusion_order_is_not_significant(self):
        value = copy.deepcopy(self.reference)
        for field in ("identity_sources", "excluded_t8103_boards", "excluded_families"):
            value["target"][field].reverse()
        self.assertEqual(target.validate(value), [])


class TargetRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        metadata = self.root / target.MAP_RELATIVE
        metadata.parent.mkdir(parents=True)
        metadata.write_text((target.ROOT / target.MAP_RELATIVE).read_text(encoding="utf-8"), encoding="utf-8")
        for entrypoint in target.ENTRYPOINTS:
            path = self.root / entrypoint
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Entrypoint\n\n" + target.DECLARATION + "\n", encoding="utf-8")

    def test_complete_fixture_and_real_repository_pass(self):
        self.assertEqual(target.validate_repository(self.root), [])
        self.assertEqual(target.validate_repository(), [])

    def test_each_entrypoint_rejects_missing_drifted_or_duplicate_declarations(self):
        for entrypoint in target.ENTRYPOINTS:
            path = self.root / entrypoint
            original = path.read_text(encoding="utf-8")
            for content in (
                "# Missing declaration\n",
                target.DECLARATION.replace("T8103/H13G", "T6000/H13S"),
                target.DECLARATION.replace("J274", "J313"),
                target.DECLARATION + "\n" + target.DECLARATION,
                target.DECLARATION + "\n" + target.DECLARATION.replace("J274", "J313"),
            ):
                with self.subTest(entrypoint=entrypoint, content=content):
                    path.write_text(content, encoding="utf-8")
                    errors = target.validate_repository(self.root)
                    self.assertTrue(any(entrypoint in error for error in errors))
            path.write_text(original, encoding="utf-8")

    def test_hidden_declaration_does_not_satisfy_visible_contract(self):
        path = self.root / "README.md"
        for before, after in (("```text\n", "\n```"), ("~~~\n", "\n~~~"), ("<!--\n", "\n-->")):
            with self.subTest(before=before):
                path.write_text(before + target.DECLARATION + after, encoding="utf-8")
                self.assertTrue(target.validate_repository(self.root))
        path.write_text("````\n```\n" + target.DECLARATION + "\n````", encoding="utf-8")
        self.assertTrue(target.validate_repository(self.root))

    def test_missing_and_non_utf8_entrypoints_are_diagnostics(self):
        for entrypoint in target.ENTRYPOINTS:
            path = self.root / entrypoint
            content = path.read_bytes()
            path.unlink()
            self.assertTrue(any(entrypoint in error for error in target.validate_repository(self.root)))
            path.write_bytes(b"\xff")
            self.assertTrue(any(entrypoint in error for error in target.validate_repository(self.root)))
            path.write_bytes(content)

    def test_missing_corrupt_and_non_object_metadata_are_diagnostics(self):
        path = self.root / target.MAP_RELATIVE
        path.unlink()
        self.assertTrue(target.validate_repository(self.root))
        for data in (b"{broken", b"\xff", b"[]", b"null"):
            with self.subTest(data=data):
                path.write_bytes(data)
                self.assertTrue(target.validate_repository(self.root))

    def test_coordinated_metadata_and_document_drift_is_rejected(self):
        path = self.root / target.MAP_RELATIVE
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["soc"] = "T6000"
        raw["target"]["board_id"] = "J313"
        path.write_text(json.dumps(raw), encoding="utf-8")
        for entrypoint in target.ENTRYPOINTS:
            (self.root / entrypoint).write_text(
                target.DECLARATION.replace("T8103", "T6000").replace("J274", "J313"), encoding="utf-8")
        errors = target.validate_repository(self.root)
        self.assertTrue(any("soc:" in error for error in errors))
        self.assertTrue(any("README.md" in error for error in errors))

    def test_cli_success_failure_and_default_root_are_cwd_independent(self):
        script = target.ROOT / "tools/validate_target.py"
        command = [sys.executable, str(script)]
        for args in ([], ["--root", str(self.root)]):
            result = subprocess.run(command + args, cwd=self.root, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Valid P001 target", result.stdout)
        (self.root / "README.md").unlink()
        result = subprocess.run(command + ["--root", str(self.root)], cwd=self.root,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("README.md", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
