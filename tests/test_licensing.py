"""P006 source-boundary checks using adversarial manifests and real file trees.

All firmware, binary and third-party examples below are synthetic test bytes.
Passing this suite establishes inventory behavior, not copyright ownership.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import validate_licensing as licensing


class LicensingPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((licensing.ROOT / licensing.MANIFEST).read_text(encoding="utf-8"))

    def test_reviewed_manifest_passes(self):
        self.assertEqual(licensing.validate(self.reference), [])

    def test_malformed_policy_reports_errors_without_crashing(self):
        for value in (None, [], "policy", 1, True):
            with self.subTest(value=value):
                self.assertTrue(licensing.validate(value))
        for field, values in (
            ("schema_version", (None, True, 1.0, "1", 2)),
            ("phase", (None, "P007", [], {})),
            ("reviewed_on", (None, "2026-02-30", "2026-10-23T00:00:00", [])),
            ("baseline_commit", (None, "main", "a" * 39, "z" * 40, [])),
            ("project_license", (None, "MIT", [], True)),
            ("project_files", (None, "README.md", {}, True)),
            ("boundaries", (None, [], "reviewed", True)),
            ("dependencies", (None, {}, "qemu", True)),
            ("review_inputs", (None, {}, "tools/setup_qemu.sh", True)),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken[field] = value
                    self.assertTrue(licensing.validate(broken))

    def test_unknown_and_missing_fields_cannot_hide_exceptions(self):
        for field in self.reference:
            with self.subTest(missing=field):
                broken = copy.deepcopy(self.reference)
                del broken[field]
                self.assertTrue(licensing.validate(broken))
        broken = copy.deepcopy(self.reference)
        broken["allow_unreviewed_assets"] = True
        self.assertTrue(licensing.validate(broken))
        for field in ("dependencies", "review_inputs"):
            with self.subTest(nested=field):
                broken = copy.deepcopy(self.reference)
                broken[field][0]["exception"] = "ignore this component"
                self.assertTrue(licensing.validate(broken))

    def test_paths_cannot_escape_or_alias_the_source_tree(self):
        for path in (
            "", "/tmp/firmware", "../firmware", "docs/../../firmware", "./README.md",
            "docs/../README.md", "docs//note.md", "docs/./note.md", "docs/",
            "docs\\note.md", "C:/firmware", "docs/*.md", "docs/note\x00.md",
            "docs/note\n.md", [], {},
        ):
            with self.subTest(path=path):
                broken = copy.deepcopy(self.reference)
                broken["project_files"].append(path)
                self.assertTrue(licensing.validate(broken))

    def test_files_and_dependency_records_cannot_be_duplicated(self):
        for field in ("project_files", "dependencies", "review_inputs"):
            with self.subTest(field=field):
                broken = copy.deepcopy(self.reference)
                broken[field].append(copy.deepcopy(broken[field][0]))
                self.assertTrue(licensing.validate(broken))

    def test_mit_scope_and_proprietary_exclusion_cannot_be_weakened(self):
        for field, value in (("spdx", "GPL-2.0-only"), ("notice", "docs/LICENSE"),
                             ("sha256", "0" * 63)):
            with self.subTest(field=field):
                broken = copy.deepcopy(self.reference)
                broken["project_license"][field] = value
                self.assertTrue(licensing.validate(broken))
        for boundary in self.reference["boundaries"]:
            with self.subTest(boundary=boundary):
                broken = copy.deepcopy(self.reference)
                broken["boundaries"][boundary] = "all-covered-by-MIT"
                self.assertTrue(licensing.validate(broken))

    def test_external_components_cannot_be_declared_shipped(self):
        for index, dependency in enumerate(self.reference["dependencies"]):
            for flag in (True, 0, 1, "false", None, [], {}):
                with self.subTest(dependency=dependency["id"], flag=flag):
                    broken = copy.deepcopy(self.reference)
                    broken["dependencies"][index]["shipped"] = flag
                    self.assertTrue(licensing.validate(broken))

    def test_required_component_groups_cannot_disappear_from_review(self):
        for identifier in ("qemu", "qemu-firmware", "asahi-docs"):
            with self.subTest(dependency=identifier):
                broken = copy.deepcopy(self.reference)
                broken["dependencies"] = [entry for entry in broken["dependencies"]
                                          if entry["id"] != identifier]
                self.assertTrue(licensing.validate(broken))

    def test_dependency_evidence_and_use_sites_must_exist(self):
        for field, values in (
            ("id", (None, [], {})),
            ("kind", (None, "bundled", [], {})),
            ("license", (None, "", [], {})),
            ("sources", ([], None, ["http://example.com/license"],
                         ["https://user:secret@example.com/license"], ["https://["],
                         ["https://bad host/license"], [{}])),
            ("use_sites", ([], None, ["not-reviewed.txt"], ["../outside"], [{}])),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    broken = copy.deepcopy(self.reference)
                    broken["dependencies"][0][field] = value
                    self.assertTrue(licensing.validate(broken))

    def test_input_review_cannot_reference_unknown_dependencies_or_files(self):
        for field, value in (
            ("path", "missing-script.sh"), ("path", "../outside"),
            ("sha256", "g" * 64), ("sha256", []),
            ("dependencies", ["unknown-component"]), ("dependencies", []),
            ("dependencies", [{}]),
        ):
            with self.subTest(field=field, value=value):
                broken = copy.deepcopy(self.reference)
                broken["review_inputs"][0][field] = value
                self.assertTrue(licensing.validate(broken))

    def test_required_review_input_cannot_be_removed(self):
        for index, entry in enumerate(self.reference["review_inputs"]):
            with self.subTest(path=entry["path"]):
                broken = copy.deepcopy(self.reference)
                broken["review_inputs"].pop(index)
                self.assertTrue(licensing.validate(broken))

    def test_duplicate_nested_sources_use_sites_and_components_are_rejected(self):
        for field in ("sources", "use_sites"):
            with self.subTest(field=field):
                broken = copy.deepcopy(self.reference)
                values = broken["dependencies"][0][field]
                values.append(values[0])
                self.assertTrue(licensing.validate(broken))
        broken = copy.deepcopy(self.reference)
        values = broken["review_inputs"][0]["dependencies"]
        values.append(values[0])
        self.assertTrue(licensing.validate(broken))

    def test_reviewed_core_license_sources_cannot_be_replaced_with_generic_links(self):
        for identifier in ("qemu", "linux", "asahi-docs"):
            with self.subTest(dependency=identifier):
                broken = copy.deepcopy(self.reference)
                entry = next(item for item in broken["dependencies"] if item["id"] == identifier)
                entry["sources"] = ["https://example.com/unspecified-license"]
                self.assertTrue(licensing.validate(broken))

    def test_core_licenses_cannot_be_relabelled_or_lose_file_specific_boundaries(self):
        for identifier, claimed_license in (
            ("qemu", "MIT"),
            ("linux", "GPL-3.0-only"),
            ("asahi-docs", "Open source documentation"),
            ("m1n1", "MIT"),
            ("busybox", "GPL-2.0-or-later for the whole distribution"),
        ):
            with self.subTest(dependency=identifier, claimed_license=claimed_license):
                broken = copy.deepcopy(self.reference)
                entry = next(item for item in broken["dependencies"] if item["id"] == identifier)
                entry["license"] = claimed_license
                self.assertTrue(licensing.validate(broken))


class LicensingRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent / "snapshot"
        self.root.mkdir()
        self.policy = json.loads((licensing.ROOT / licensing.MANIFEST).read_text(encoding="utf-8"))
        for name in self.policy["project_files"]:
            source = licensing.ROOT / name
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

    def write_policy(self):
        (self.root / licensing.MANIFEST).write_text(
            json.dumps(self.policy, indent=2) + "\n", encoding="utf-8")

    def classify(self, path):
        self.policy["project_files"].append(path)
        self.policy["project_files"].sort()
        self.write_policy()

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def init_git(self):
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("add", "--all")

    def errors(self, *, archive=True):
        return licensing.validate_repository(self.root, archive=archive)

    def assert_rejected(self, *, archive=True):
        errors = self.errors(archive=archive)
        self.assertTrue(errors, "unreviewed or unsafe source tree was accepted")
        return errors

    def cli(self, *arguments, env=None):
        return subprocess.run(
            [sys.executable, str(licensing.ROOT / "tools/validate_licensing.py"),
             "--root", str(self.root), *arguments],
            cwd=self.parent, env=env, capture_output=True, text=True, timeout=20)

    def test_real_repository_and_clean_archive_pass(self):
        # The test suite also runs from a clean source export with python -B.
        # Production validation still requires the caller to select --archive.
        exported = not (licensing.ROOT / ".git").exists()
        self.assertEqual(licensing.validate_repository(archive=exported), [])
        self.assertEqual(self.errors(), [])

    def test_new_independent_text_file_needs_explicit_review(self):
        name = "tools/new_independent_tool.py"
        (self.root / name).write_text("# Independently authored synthetic fixture.\n", encoding="utf-8")
        self.assert_rejected()
        self.classify(name)
        self.assertEqual(self.errors(), [])

    def test_deleted_file_and_stale_inventory_are_rejected(self):
        (self.root / "README.md").unlink()
        self.assert_rejected()
        self.classify("docs/nonexistent-review.md")
        self.assert_rejected()

    def test_license_notice_change_is_rejected(self):
        with (self.root / "LICENSE").open("a", encoding="utf-8") as output:
            output.write("\nExcept all imported material is relicensed here.\n")
        self.assert_rejected()

    def test_each_dependency_input_change_requires_new_review(self):
        for entry in self.policy["review_inputs"]:
            with self.subTest(path=entry["path"]):
                path = self.root / entry["path"]
                original = path.read_bytes()
                path.write_bytes(original + b"\n# Synthetic new dependency declaration\n")
                self.assert_rejected()
                path.write_bytes(original)
        self.assertEqual(self.errors(), [])

    def test_binary_payload_disguised_as_reviewed_text_is_rejected(self):
        name = "docs/imported-note.md"
        self.classify(name)
        for content in (b"\x7fELF\x02\x01\x00synthetic", b"text\x00payload", b"\xff\xfeinvalid"):
            with self.subTest(content=content):
                (self.root / name).write_bytes(content)
                self.assert_rejected()

    def test_non_mit_license_header_cannot_hide_in_project_classification(self):
        name = "tools/independent_fixture.py"
        self.classify(name)
        path = self.root / name
        path.write_text("# SPDX-License-Identifier: MIT\n", encoding="utf-8")
        self.assertEqual(self.errors(), [])
        path.write_text("# SPDX-License-Identifier: GPL-2.0-only\n", encoding="utf-8")
        self.assert_rejected()
        path.write_text("# Discuss GPL-2.0-only as an external license, not this file's grant.\n",
                        encoding="utf-8")
        self.assertEqual(self.errors(), [])

    def test_text_size_limit_is_enforced_before_accepting_large_files(self):
        name = "docs/large-fixture.md"
        self.classify(name)
        (self.root / name).write_bytes(b"x" * (2 * 1024 * 1024 + 1))
        self.assert_rejected()

    def test_prohibited_assets_cannot_be_relabelled_as_project_files(self):
        for name in ("synthetic.ipsw", "synthetic.im4p", "synthetic.img",
                     "vendor/import.py", "third_party/import.py", "firmware/note.txt"):
            with self.subTest(name=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic fixture, no proprietary data\n", encoding="utf-8")
                self.classify(name)
                self.assert_rejected()
                self.policy["project_files"].remove(name)
                self.write_policy()
                path.unlink()

    def test_git_mode_checks_untracked_source_and_ignores_only_local_outputs(self):
        self.init_git()
        self.assertEqual(self.errors(archive=False), [])
        (self.root / "local-only.ipsw").write_text("synthetic local input\n", encoding="utf-8")
        self.assertEqual(self.errors(archive=False), [])
        (self.root / "unreviewed.py").write_text("# Synthetic untracked source.\n", encoding="utf-8")
        self.assert_rejected(archive=False)

    def test_force_added_ignored_asset_is_not_hidden_by_gitignore(self):
        self.init_git()
        (self.root / "synthetic.ipsw").write_text("synthetic fixture\n", encoding="utf-8")
        self.git("add", "--force", "synthetic.ipsw")
        self.assert_rejected(archive=False)
        self.classify("synthetic.ipsw")
        self.assert_rejected(archive=False)

    def test_archive_checks_ignored_outputs_and_rejects_git_metadata(self):
        (self.root / "synthetic.ipsw").write_text("synthetic fixture\n", encoding="utf-8")
        self.assert_rejected()
        (self.root / "synthetic.ipsw").unlink()
        self.init_git()
        self.assert_rejected()

    def test_symlink_file_is_rejected_even_with_identical_reviewed_bytes(self):
        source = self.root / "README.md"
        outside = self.parent / "outside.md"
        source.replace(outside)
        source.symlink_to(outside)
        self.assert_rejected()

    def test_parent_symlink_cannot_redirect_an_inventory_read(self):
        outside = self.parent / "outside-tools"
        (self.root / "tools").replace(outside)
        (self.root / "tools").symlink_to(outside, target_is_directory=True)
        self.assert_rejected()

    def test_gitlink_submodule_requires_a_separate_import_review(self):
        self.init_git()
        self.git("update-index", "--add", "--cacheinfo", "160000",
                 "1234567890123456789012345678901234567890", "external-module")
        self.assert_rejected(archive=False)

    def test_default_mode_does_not_mistake_ancestor_git_for_snapshot(self):
        subprocess.run(["git", "-C", str(self.parent), "init", "--quiet"], check=True,
                       capture_output=True, text=True)
        self.assert_rejected(archive=False)
        self.assertEqual(self.errors(), [])

    def test_broken_git_metadata_does_not_fall_back_to_archive_scan(self):
        (self.root / ".git").mkdir()
        self.assert_rejected(archive=False)

    def test_duplicate_json_keys_and_invalid_json_fail_cleanly(self):
        path = self.root / licensing.MANIFEST
        original = path.read_text(encoding="utf-8")
        for content in ('{"schema_version": 1, "schema_version": 1,',
                        original.replace('"schema_version": 1',
                                         '"schema_version": 1, "schema_version": 1', 1),
                        '{"project_files": ['):
            with self.subTest(content=content[:80]):
                path.write_text(content, encoding="utf-8")
                self.assert_rejected()

    def test_cli_archive_works_from_another_directory_and_reports_failures(self):
        accepted = self.cli("--archive")
        self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
        (self.root / "unreviewed.py").write_text("# Synthetic fixture.\n", encoding="utf-8")
        rejected = self.cli("--archive")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertNotIn("Traceback", rejected.stdout + rejected.stderr)

    def test_excessively_nested_json_reports_a_clean_error(self):
        (self.root / licensing.MANIFEST).write_text(
            "[" * 20000 + "0" + "]" * 20000, encoding="utf-8")
        self.assert_rejected()
        rejected = self.cli("--archive")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("cannot read licensing inventory", rejected.stdout)
        self.assertNotIn("Traceback", rejected.stdout + rejected.stderr)

    def test_missing_git_fails_closed_with_a_clear_cli_error(self):
        self.init_git()
        result = self.cli(env={**os.environ, "PATH": ""})
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        self.assertIn("git", (result.stdout + result.stderr).lower())


if __name__ == "__main__":
    unittest.main()
