#!/usr/bin/env python3
"""Check P007 contribution instructions; optionally inspect a local main checkout.

The default is an offline, bounded documentation/workflow check, suitable for
source archives and detached CI checkouts. --checkout adds read-only Git checks.
Neither mode fetches, changes refs, runs tests, certifies review or queries CI.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_LINES = (
    "- `main` is the sole authoritative development branch.",
    "- Routine contributions do not require auxiliary branches or pull requests.",
    "- Review the exact staged change and test the exact tree that will be committed.",
    "- Preserve existing work and published history; never force-push or rewrite published commits.",
    "- Publish with an explicit fast-forward push to `refs/heads/main`.",
    "- A pushed commit is verified only after both required jobs pass for that exact commit SHA.",
)
REQUIRED_SECTIONS = (
    "## Review and stage", "## Test the staged tree",
    "## Commit and publish", "## Concurrent work and failures",
)
ENTRYPOINT_LINKS = {
    "README.md": "CONTRIBUTING.md",
    "AGENTS.md": "CONTRIBUTING.md",
    "docs/DEVELOPMENT.md": "../CONTRIBUTING.md",
}
WORKFLOW = ".github/workflows/verify.yml"
WORKFLOW_EVENTS = (
    "on:\n  push:\n    branches: [main]\n"
    "  pull_request:\n    branches: [main]\n"
)
OPERATIONS = (
    "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG",
    "rebase-merge", "rebase-apply", "sequencer",
)


def _markdown(text: str) -> tuple[str, list[str]]:
    """Separate visible prose and runnable shell examples, not a Markdown parser."""
    text = re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.DOTALL)
    prose: list[str] = []
    blocks: list[str] = []
    block: list[str] = []
    fence = ""
    shell = False
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            token, label = match.groups()
            if not fence:
                fence = token
                shell = label.strip().lower() in {"", "sh", "bash", "shell", "console"}
                block = []
                continue
            if token[0] == fence[0] and len(token) >= len(fence) and not label.strip():
                if shell:
                    blocks.append("\n".join(block))
                fence = ""
                continue
        if fence:
            block.append(line)
        else:
            prose.append(line)
    if fence and shell:
        blocks.append("\n".join(block))
    return "\n".join(prose), blocks


def validate_instructions(text: str, path: str) -> list[str]:
    """Reject common contradictory imperatives and unsafe shell examples.

    This is deliberately bounded lint, not semantic analysis or a shell parser.
    Human review must still check all instructions, scripts and quoted examples.
    """
    prose, blocks = _markdown(text)
    errors: list[str] = []
    for line in prose.splitlines():
        plain = re.sub(r"[`*_]", "", line).strip()
        imperative = re.search(
            r"\b(?:must|need to|required to)\s+(?:first\s+)?"
            r"(?:create|open|use|submit)\s+(?:(?:a|an|the|your)\s+)?"
            r"(?:(?:new|feature|topic|auxiliary|separate)\s+)*(?:branch|pull request)\b",
            plain, re.IGNORECASE,
        )
        required = re.search(r"\b(?:branches|branch|pull requests?)\s+(?:is|are)\s+"
                             r"(?:required|mandatory)\b", plain, re.IGNORECASE)
        direct = re.match(r"(?:[-+]\s+|\d+[.)]\s+)?(?:Please\s+)?(?:Create|Open)\s+"
                          r"(?:a|an|the|your)\s+(?:(?:new|feature|topic|auxiliary|separate)\s+)*"
                          r"(?:branch|pull request)\b", plain, re.IGNORECASE)
        for match in (imperative, required, direct):
            if match and not re.search(r"\b(?:not|no|never)\b", plain[:match.start()], re.IGNORECASE):
                errors.append(f"{path}: auxiliary-branch/pull-request requirement: {plain}")
                break

    command = re.compile(r"\bgit(?:\s+-[Cc]\s+\S+)*\s+"
                         r"(switch|checkout|branch|push|reset|clean|commit)\b([^\n;&|]*)")
    for block in blocks:
        block = re.sub(r"\\\n\s*", " ", block)
        for line in block.splitlines():
            if line.lstrip().startswith("#"):
                continue
            for match in command.finditer(line):
                verb, tail = match.groups()
                try:
                    args = shlex.split(tail, comments=True)
                except ValueError:
                    errors.append(f"{path}: malformed Git command example")
                    continue
                unsafe = False
                if verb in {"switch", "checkout"}:
                    flags = {"c", "C"} if verb == "switch" else {"b", "B"}
                    unsafe = any((arg.startswith("-") and not arg.startswith("--")
                                  and bool(flags.intersection(arg[1:]))) or arg.split("=", 1)[0] in
                                 {"--create", "--force-create", "--orphan"} for arg in args)
                elif verb == "branch":
                    unsafe = bool(args) and not any(arg in {"--show-current", "--list", "-l", "-a", "-r"}
                                                   for arg in args)
                elif verb == "push":
                    unsafe = any(arg.startswith(("--force", "+")) or arg in
                                 {"--mirror", "--all", "--delete", "--prune", "--tags"}
                                 or (arg.startswith("-") and not arg.startswith("--") and "f" in arg)
                                 for arg in args)
                    positional = [arg for arg in args if not arg.startswith("-")]
                    if len(positional) != 2 or not positional[-1].endswith(":refs/heads/main"):
                        errors.append(f"{path}: push example must have one explicit target, refs/heads/main")
                elif verb == "reset":
                    unsafe = "--hard" in args
                elif verb == "clean":
                    unsafe = any(arg == "--force" or (arg.startswith("-") and "f" in arg) for arg in args)
                elif verb == "commit":
                    unsafe = _changes_commit_contents(args)
                if unsafe:
                    errors.append(f"{path}: unsafe or auxiliary-branch Git example: git {verb}{tail}")
    return errors


def _changes_commit_contents(args: list[str]) -> bool:
    """Recognize common commit flags/path arguments that bypass the tested index."""
    consume_value = False
    for arg in args:
        if consume_value:
            consume_value = False
            continue
        option = arg.split("=", 1)[0]
        if option in {"--all", "--include", "--only", "--amend", "--interactive",
                      "--patch", "--pathspec-from-file"}:
            return True
        if option in {"--message", "--file", "--reuse-message", "--reedit-message",
                      "--author", "--date", "--cleanup", "--trailer"}:
            consume_value = "=" not in arg
        elif arg.startswith("-") and not arg.startswith("--"):
            for index, flag in enumerate(arg[1:], 1):
                if flag in "aiop":
                    return True
                if flag in "mFcCS":
                    consume_value = flag != "S" and index == len(arg) - 1
                    break
        elif not arg.startswith("--"):
            return True
    return False


def validate_repository(root: Path = ROOT) -> list[str]:
    """Check the fixed visible policy, its entrypoint links and supported CI form."""
    errors: list[str] = []
    documents: dict[str, str] = {}
    for path in ("CONTRIBUTING.md", *ENTRYPOINT_LINKS, WORKFLOW):
        try:
            documents[path] = (root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path}: cannot read policy input: {exc}")
    if "CONTRIBUTING.md" in documents:
        prose, _ = _markdown(documents["CONTRIBUTING.md"])
        lines = prose.splitlines()
        for line in (*CONTRACT_LINES, *REQUIRED_SECTIONS):
            if lines.count(line) != 1:
                errors.append(f"CONTRIBUTING.md: expected exactly one visible policy line: {line}")
    for path, target in ENTRYPOINT_LINKS.items():
        if path in documents:
            prose, _ = _markdown(documents[path])
            if not re.search(r"\[[^\]\n]+\]\(" + re.escape(target) + r"(?:#[^\s)]*)?\)", prose):
                errors.append(f"{path}: missing visible contribution link to {target}")
    for path, text in documents.items():
        if path != WORKFLOW:
            errors.extend(validate_instructions(text, path))
    if WORKFLOW in documents:
        text = documents[WORKFLOW]
        events = re.findall(r"^on:\n(?:[ \t]+[^\n]*\n|\n)*", text, re.MULTILINE)
        if len(events) != 1 or events[0].rstrip() != WORKFLOW_EVENTS.rstrip():
            errors.append(f"{WORKFLOW}: expected main-only push and optional main-targeted pull_request triggers")
        command = "python3 tools/validate_branch_policy.py"
        if not re.search(r"^\s+" + re.escape(command) + r"\s*$", text, re.MULTILINE):
            errors.append(f"{WORKFLOW}: missing offline branch-policy validation step")
    return errors


class GitCheckError(Exception):
    """A failed local read, not permission to repair or change the checkout."""


def _git(root: Path, *args: str, allowed: tuple[int, ...] = (0,),
         input_data: bytes | None = None) -> subprocess.CompletedProcess:
    # Repository-selecting environment variables must not redirect this check.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
                "GIT_NO_LAZY_FETCH": "1", "LC_ALL": "C"})
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitCheckError(f"cannot read Git checkout: {exc}") from exc
    if result.returncode not in allowed:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitCheckError(f"git {args[0]} failed ({result.returncode}): {message}")
    return result


def validate_checkout(root: Path = ROOT) -> list[str]:
    """Read-only local preflight; origin/main is cached, not a remote observation."""
    try:
        root = root.resolve()
    except (OSError, RuntimeError) as exc:
        return [f"checkout: cannot resolve selected root: {exc}"]
    if not (root / ".git").exists():
        return ["checkout: selected root must have its own .git directory or worktree file"]
    errors: list[str] = []
    try:
        top = _git(root, "rev-parse", "--show-toplevel").stdout.decode().strip()
        if Path(top).resolve() != root:
            return ["checkout: selected root is not the Git worktree top level"]
        branch = _git(root, "symbolic-ref", "--quiet", "HEAD", allowed=(0, 1))
        if branch.returncode or branch.stdout.strip() != b"refs/heads/main":
            errors.append("checkout: development requires attached main; detached or other branches are not publishable")
        head = _git(root, "rev-parse", "--verify", "HEAD^{commit}", allowed=(0, 128))
        if head.returncode:
            return errors + ["checkout: HEAD must identify an existing commit (unborn checkout)"]
        if _git(root, "ls-files", "--unmerged", "-z").stdout:
            errors.append("checkout: unresolved index conflicts must be reviewed and resolved")
        for operation in OPERATIONS:
            location = os.fsdecode(_git(root, "rev-parse", "--git-path", operation).stdout).rstrip("\n")
            path = Path(location)
            if not path.is_absolute():
                path = root / path
            if path.exists():
                errors.append(f"checkout: unfinished Git operation {operation}; preserve work and resolve it first")
        # Even a quiet diff can execute attribute clean/process commands. Fail
        # before that read rather than run a configured program with side effects.
        filters = _git(root, "config", "--name-only", "--get-regexp",
                       r"^filter\..*\.(clean|process)$", allowed=(0, 1))
        configured = {key[len(b"filter."):].rsplit(b".", 1)[0] for key in filters.stdout.splitlines()}
        if configured:
            paths = _git(root, "ls-files", "--cached", "-z").stdout
            attributes = _git(root, "check-attr", "-z", "--stdin", "filter", input_data=paths).stdout
            active = set(attributes.rstrip(b"\0").split(b"\0")[2::3])
            if active.intersection(configured):
                return errors + ["checkout: active clean/process filters need separate review; read-only preflight stopped"]
        if _git(root, "diff", "--no-ext-diff", "--no-textconv", "--quiet", "--exit-code",
                "--ignore-submodules=none", allowed=(0, 1)).returncode:
            errors.append("checkout: unstaged tracked changes; review and stage the intended complete change")
        if _git(root, "ls-files", "--others", "--exclude-standard", "-z").stdout:
            errors.append("checkout: nonignored untracked files; review them before verifying the staged tree")
        remote = _git(root, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}", allowed=(0, 128))
        if remote.returncode:
            errors.append("checkout: cached origin/main is missing; review origin and fetch main first")
        elif _git(root, "merge-base", "--is-ancestor", "refs/remotes/origin/main", "HEAD",
                  allowed=(0, 1)).returncode:
            errors.append("checkout: cached origin/main is not an ancestor of HEAD; integrate, review and retest")
    except (GitCheckError, UnicodeError, OSError) as exc:
        errors.append(f"checkout: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository snapshot to inspect")
    parser.add_argument("--checkout", action="store_true", help="also require a ready local main checkout")
    args = parser.parse_args()
    errors = validate_repository(args.root)
    if args.checkout:
        errors.extend(validate_checkout(args.root))
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Valid P007 policy: one authoritative main branch, review and tested commits; no required auxiliary branches")
        if args.checkout:
            print("Local main preflight passed using cached origin/main; remote freshness and CI were not checked")
        print("Bounded policy checks do not certify review, executed tests, remote enforcement or emulation fidelity")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
