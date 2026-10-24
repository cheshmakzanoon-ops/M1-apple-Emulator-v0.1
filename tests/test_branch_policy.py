"""P007 contribution policy and read-only checkout checks.

Git states are built in temporary repositories. No test contacts a remote or
changes the branch, index or history of the project checkout.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import validate_branch_policy as policy


class InstructionPolicyTests(unittest.TestCase):
    def test_auxiliary_branch_commands_are_rejected(self):
        for command in (
            "git switch -c feature", "git switch -C feature",
            "git checkout -b feature", "git checkout -B feature",
            "git switch -cfeature", "git checkout -bfeature",
        ):
            with self.subTest(command=command):
                self.assertTrue(policy.validate_instructions(
                    f"```sh\n{command}\n```\n", "CONTRIBUTING.md"))

    def test_destructive_publication_commands_are_rejected(self):
        for command in (
            "git push --force origin main", "git push -f origin main",
            "git push --force-with-lease origin main",
            "git push origin +HEAD:refs/heads/main", "git reset --hard origin/main",
            "git push origin HEAD:refs/heads/main refs/heads/feature:refs/heads/feature",
            "git commit -a -m change", "git commit -am change",
            "git commit --all -m change", "git commit -i tracked.txt -m change",
            "git commit --include tracked.txt -m change",
            "git commit -o tracked.txt -m change", "git commit --only tracked.txt -m change",
            "git commit -m change -- tracked.txt", "git commit tracked.txt",
        ):
            with self.subTest(command=command):
                self.assertTrue(policy.validate_instructions(
                    f"```bash\n{command}\n```\n", "CONTRIBUTING.md"))

    def test_mandatory_auxiliary_branch_and_pull_request_are_rejected(self):
        for text in (
            "Contributors must create a feature branch before making changes.",
            "You must open a pull request before pushing.",
        ):
            with self.subTest(text=text):
                self.assertTrue(policy.validate_instructions(text, "AGENTS.md"))

    def test_safe_commands_negative_prose_and_optional_review_are_allowed(self):
        text = """Do not create a feature branch. Pull requests are not required.
An existing pull request may be inspected for review.
```sh
git switch main
git fetch origin
git merge --ff-only origin/main
git diff --cached --check
git push origin HEAD:refs/heads/main
git revert COMMIT
```
"""
        self.assertEqual(policy.validate_instructions(text, "CONTRIBUTING.md"), [])


class BranchPolicyRepositoryTests(unittest.TestCase):
    FILES = (
        "CONTRIBUTING.md", "README.md", "AGENTS.md", "docs/DEVELOPMENT.md",
        ".github/workflows/verify.yml",
    )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent / "snapshot"
        self.root.mkdir()
        for name in self.FILES:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(policy.ROOT / name, destination)

    def cli(self, *arguments, env=None):
        return subprocess.run(
            [sys.executable, str(policy.ROOT / "tools/validate_branch_policy.py"),
             "--root", str(self.root), *arguments],
            cwd=self.parent, env=env, capture_output=True, text=True, timeout=20,
        )

    def test_real_repository_clean_export_and_crlf_pass_without_git(self):
        self.assertEqual(policy.validate_repository(), [])
        self.assertFalse((self.root / ".git").exists())
        self.assertEqual(policy.validate_repository(self.root), [])
        for name in self.FILES:
            path = self.root / name
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(policy.validate_repository(self.root), [])

    def test_each_contract_line_must_be_visible_once(self):
        path = self.root / "CONTRIBUTING.md"
        original = path.read_text(encoding="utf-8")
        for line in policy.CONTRACT_LINES:
            for replacement in (
                "", f"{line}\n{line}", f"<!--\n{line}\n-->",
                f"```text\n{line}\n```", f"~~~text\n{line}\n~~~",
            ):
                with self.subTest(line=line, replacement=replacement):
                    path.write_text(original.replace(line, replacement), encoding="utf-8")
                    self.assertTrue(policy.validate_repository(self.root))
        path.write_text(original, encoding="utf-8")

    def test_each_workflow_section_is_required(self):
        path = self.root / "CONTRIBUTING.md"
        original = path.read_text(encoding="utf-8")
        for heading in policy.REQUIRED_SECTIONS:
            with self.subTest(heading=heading):
                path.write_text(original.replace(heading, "Removed section"), encoding="utf-8")
                self.assertTrue(policy.validate_repository(self.root))
        path.write_text(original, encoding="utf-8")

    def test_every_entrypoint_links_to_contribution_workflow(self):
        for name, target in policy.ENTRYPOINT_LINKS.items():
            path = self.root / name
            original = path.read_text(encoding="utf-8")
            with self.subTest(name=name):
                path.write_text(original.replace(f"]({target})", "](missing.md)"), encoding="utf-8")
                self.assertTrue(policy.validate_repository(self.root))
            path.write_text(original, encoding="utf-8")

    def test_all_contribution_entrypoints_are_linted(self):
        for name in ("CONTRIBUTING.md", *policy.ENTRYPOINT_LINKS):
            path = self.root / name
            original = path.read_text(encoding="utf-8")
            with self.subTest(name=name):
                path.write_text(original + "\n```sh\ngit switch -c feature\n```\n", encoding="utf-8")
                self.assertTrue(policy.validate_repository(self.root))
            path.write_text(original, encoding="utf-8")

    def test_ci_requires_main_push_and_the_policy_check(self):
        path = self.root / ".github/workflows/verify.yml"
        original = path.read_text(encoding="utf-8")
        self.assertIn("branches: [main]", original)
        self.assertIn("python3 tools/validate_branch_policy.py", original)
        for changed in (
            original.replace("branches: [main]", "branches: [develop]"),
            original.replace("branches: [main]", "branches: [main, develop]"),
            original.replace("python3 tools/validate_branch_policy.py", "python3 tools/validate_target.py"),
        ):
            with self.subTest(changed=changed[:100]):
                path.write_text(changed, encoding="utf-8")
                self.assertTrue(policy.validate_repository(self.root))
        path.write_text(original, encoding="utf-8")

    def test_missing_non_utf8_and_nonfile_documents_are_diagnostics(self):
        for name in self.FILES:
            path = self.root / name
            original = path.read_bytes()
            with self.subTest(name=name, kind="missing"):
                path.unlink()
                self.assertTrue(policy.validate_repository(self.root))
            with self.subTest(name=name, kind="directory"):
                path.mkdir()
                self.assertTrue(policy.validate_repository(self.root))
                path.rmdir()
            with self.subTest(name=name, kind="encoding"):
                path.write_bytes(b"\xff")
                self.assertTrue(policy.validate_repository(self.root))
            path.write_bytes(original)

    def test_cli_default_and_alternate_root_work_from_another_directory(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        default = subprocess.run(
            [sys.executable, str(policy.ROOT / "tools/validate_branch_policy.py")],
            cwd=self.parent, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(default.returncode, 0, default.stdout + default.stderr)
        (self.root / "CONTRIBUTING.md").unlink()
        result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONTRIBUTING.md", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class CheckoutPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent / "checkout"
        self.root.mkdir()
        self.env = os.environ.copy()
        # Isolate fixture identity/configuration from the developer's host.
        for name in tuple(self.env):
            if name.startswith("GIT_"):
                del self.env[name]
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.name", "Synthetic Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.filemode", "true")
        (self.root / "tracked.txt").write_text("base\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("build/\n", encoding="utf-8")
        self.git("add", ".gitignore", "tracked.txt")
        self.git("commit", "--quiet", "-m", "Synthetic baseline")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", self.base)

    def git(self, *arguments, input=None, root=None):
        return subprocess.run(
            ["git", "-C", str(root or self.root), *arguments], input=input,
            env=self.env, capture_output=True, text=True, check=True, timeout=15,
        )

    def errors(self):
        return policy.validate_checkout(self.root)

    def fingerprint(self):
        paths = (".git/HEAD", ".git/index", "tracked.txt")
        return (
            tuple(hashlib.sha256((self.root / name).read_bytes()).hexdigest() for name in paths),
            self.git("show-ref").stdout,
            self.git("status", "--porcelain=v1", "-z").stdout,
        )

    def test_main_staged_changes_extra_refs_and_guard_read_only(self):
        (self.root / "tracked.txt").write_text("reviewed change\n", encoding="utf-8")
        (self.root / "new file.txt").write_text("reviewed addition\n", encoding="utf-8")
        self.git("add", "tracked.txt", "new file.txt")
        self.git("branch", "unrelated-existing-ref")
        before = self.fingerprint()
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.fingerprint(), before)

    def test_non_main_detached_and_unborn_heads_are_rejected(self):
        self.git("switch", "--quiet", "-c", "feature")
        self.assertTrue(self.errors())
        self.git("switch", "--quiet", "--detach")
        self.assertTrue(self.errors())
        unborn = self.parent / "unborn"
        unborn.mkdir()
        self.git("init", "--quiet", "--initial-branch=main", root=unborn)
        self.assertTrue(policy.validate_checkout(unborn))

    def test_non_repository_and_nested_roots_cannot_use_an_ancestor(self):
        self.assertTrue(policy.validate_checkout(self.parent))
        nested = self.root / "nested"
        nested.mkdir()
        self.assertTrue(policy.validate_checkout(nested))
        self.assertTrue(policy.validate_checkout(self.parent / "absent"))
        loop = self.parent / "loop"
        loop.symlink_to("loop")
        self.assertTrue(policy.validate_checkout(loop))
        result = subprocess.run(
            [sys.executable, str(policy.ROOT / "tools/validate_branch_policy.py"),
             "--root", str(loop), "--checkout"],
            cwd=self.parent, capture_output=True, text=True, timeout=20,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_read_only_guard_does_not_execute_fsmonitor_hooks(self):
        hook = self.parent / "synthetic-fsmonitor.sh"
        marker = self.parent / "hook-executed"
        hook.write_text(
            "#!/bin/sh\nprintf ran > " + shlex.quote(str(marker)) + "\nprintf 'token\\0'\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        self.git("config", "core.fsmonitor", str(hook))
        self.assertEqual(self.errors(), [])
        self.assertFalse(marker.exists(), "read-only guard executed the configured fsmonitor hook")

    def test_configured_clean_and_process_filters_are_rejected_before_execution(self):
        hook = self.parent / "synthetic-filter.sh"
        marker = self.parent / "filter-executed"
        hook.write_text(
            "#!/bin/sh\nprintf ran > " + shlex.quote(str(marker)) + "\nexit 1\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        for kind in ("clean", "process"):
            self.git("config", f"filter.inactive.{kind}", str(hook))
        self.assertEqual(self.errors(), [], "unused filter definitions must not block a checkout")
        self.assertFalse(marker.exists())
        (self.root / ".gitattributes").write_text("tracked.txt filter=synthetic\n", encoding="utf-8")
        self.git("add", ".gitattributes")
        self.git("commit", "--quiet", "-m", "Synthetic filter attribute")
        (self.root / "tracked.txt").write_text("edit\n", encoding="utf-8")
        for kind in ("clean", "process"):
            with self.subTest(kind=kind):
                key = f"filter.synthetic.{kind}"
                self.git("config", key, str(hook))
                errors = self.errors()
                self.assertTrue(any("filter" in error.lower() for error in errors), errors)
                self.assertFalse(marker.exists(), "read-only guard executed a configured filter")
                self.git("config", "--unset", key)

    def test_git_worktree_file_is_supported(self):
        linked = self.parent / "linked"
        self.git("worktree", "add", "--quiet", "--force", str(linked), "main")
        self.assertTrue((linked / ".git").is_file())
        self.assertEqual(policy.validate_checkout(linked), [])

    def test_unresolved_index_stages_are_rejected(self):
        blob = self.git("rev-parse", "HEAD:tracked.txt").stdout.strip()
        self.git("update-index", "--index-info", input=(
            f"0 {'0' * 40}\ttracked.txt\n"
            f"100644 {blob} 1\ttracked.txt\n"
            f"100644 {blob} 2\ttracked.txt\n"
            f"100644 {blob} 3\ttracked.txt\n"
        ))
        before = self.fingerprint()
        self.assertTrue(self.errors())
        self.assertEqual(self.fingerprint(), before)

    def test_in_progress_operations_are_rejected(self):
        for name, directory in (
            ("MERGE_HEAD", False), ("CHERRY_PICK_HEAD", False),
            ("REVERT_HEAD", False), ("BISECT_LOG", False),
            ("rebase-merge", True), ("rebase-apply", True), ("sequencer", True),
        ):
            path = self.root / ".git" / name
            with self.subTest(operation=name):
                if directory:
                    path.mkdir()
                else:
                    path.write_text(self.base + "\n", encoding="utf-8")
                self.assertTrue(self.errors())
                if directory:
                    path.rmdir()
                else:
                    path.unlink()

    def test_unstaged_content_mode_and_deletion_are_rejected(self):
        path = self.root / "tracked.txt"
        path.write_text("unstaged\n", encoding="utf-8")
        self.assertTrue(self.errors())
        path.write_text("base\n", encoding="utf-8")
        path.chmod(0o755)
        self.assertTrue(self.errors())
        path.chmod(0o644)
        path.unlink()
        self.assertTrue(self.errors())

    def test_untracked_unusual_names_fail_then_staged_names_pass(self):
        for name in ("new file.txt", "new\tfile.txt", "new\nfile.txt", "-new.txt"):
            with self.subTest(name=name):
                path = self.root / name
                path.write_text("synthetic\n", encoding="utf-8")
                self.assertTrue(self.errors())
                self.git("add", "--", name)
                self.assertEqual(self.errors(), [])

    def test_ignored_outputs_are_allowed_but_tracked_ignored_edits_fail(self):
        directory = self.root / "build"
        directory.mkdir()
        path = directory / "output.txt"
        path.write_text("generated\n", encoding="utf-8")
        self.assertEqual(self.errors(), [])
        self.git("add", "--force", "build/output.txt")
        self.assertEqual(self.errors(), [])
        path.write_text("unstaged generated change\n", encoding="utf-8")
        self.assertTrue(self.errors())

    def test_cached_remote_missing_behind_and_ahead_are_distinguished(self):
        self.git("update-ref", "-d", "refs/remotes/origin/main")
        self.assertTrue(self.errors())
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.git("commit", "--quiet", "--allow-empty", "-m", "Local progress")
        self.assertEqual(self.errors(), [])
        latest = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", latest)
        self.git("reset", "--quiet", "--hard", self.base)
        self.assertTrue(self.errors())

    def test_cached_remote_divergence_is_rejected_without_changes(self):
        self.git("commit", "--quiet", "--allow-empty", "-m", "Local progress")
        tree = self.git("rev-parse", f"{self.base}^{{tree}}").stdout.strip()
        other = self.git("commit-tree", tree, "-p", self.base,
                         input="Other writer's synthetic commit\n").stdout.strip()
        self.git("update-ref", "refs/remotes/origin/main", other)
        before = self.fingerprint()
        self.assertTrue(self.errors())
        self.assertEqual(self.fingerprint(), before)

    def test_checkout_cli_missing_git_and_detached_state_are_clean_failures(self):
        # CLI validates documentation as well as checkout state.
        for name in BranchPolicyRepositoryTests.FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(policy.ROOT / name, path)
        self.git("add", "--all")
        command = [sys.executable, str(policy.ROOT / "tools/validate_branch_policy.py"),
                   "--root", str(self.root), "--checkout"]
        result = subprocess.run(command, cwd=self.parent, env=self.env,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.git("switch", "--quiet", "--detach")
        result = subprocess.run(command, cwd=self.parent, env=self.env,
                                capture_output=True, text=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        no_git = self.env | {"PATH": ""}
        result = subprocess.run(command, cwd=self.parent, env=no_git,
                                capture_output=True, text=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
