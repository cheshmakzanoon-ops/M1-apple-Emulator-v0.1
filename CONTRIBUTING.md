# Contributing on main

> Research target: Apple M1 (T8103/H13G); Mac mini (M1, 2020), J274.

## Branch and review contract

- `main` is the sole authoritative development branch.
- Routine contributions do not require auxiliary branches or pull requests.
- Review the exact staged change and test the exact tree that will be committed.
- Preserve existing work and published history; never force-push or rewrite published commits.
- Publish with an explicit fast-forward push to `refs/heads/main`.
- A pushed commit is verified only after both required jobs pass for that exact commit SHA.

A separate branch requires an explicit request from the repository owner, as
recorded in [AGENTS.md](AGENTS.md); it is never an implicit prerequisite. The
default workflow below stays on the existing `main`. Read the engineering rules,
[development guide](docs/DEVELOPMENT.md) and [licensing policy](docs/LICENSING.md)
before editing. Review can happen against a local diff, an exported source tree
or a commit permalink. Review does not depend on opening a pull request.

`python3 tools/validate_branch_policy.py` checks the published contribution
contract offline, including in an archive or a detached CI checkout.
`python3 tools/validate_branch_policy.py --checkout` additionally checks the
local Git state: the repository root, an attached `main`, no incomplete Git
operation, no unstaged tracked or nonignored untracked files, and a recorded
`origin/main` that is an ancestor of `HEAD`. Staged changes are allowed. This
read-only check does not fetch, prove remote freshness, review code or run tests.
It disables filesystem-monitor hooks and optional index writes, and rejects
active configured clean/process filters before inspecting working-file differences;
those filters can execute programs even during a quiet Git read. Use a complete
local checkout; missing objects are not fetched on demand. An unsupported local
configuration needs separate review, not an automatic reset or configuration edit.

## Review and stage

Begin in the repository root on an existing, clean `main`. Inspect
`git status --short` and `git remote -v` first. Check that both the fetch and push
URLs for `origin` identify this repository; those destinations can differ. If
work is already present, preserve it and identify its owner before continuing;
do not discard or automatically stash it. To update a clean checkout, run this
block. Every block uses a subshell so an error stops its commands without closing
your interactive shell.

```sh
(
  set -eu
  test "$(git symbolic-ref -q HEAD)" = refs/heads/main
  git diff --quiet
  git diff --cached --quiet
  test -z "$(git ls-files --others --exclude-standard)"
  git fetch origin refs/heads/main:refs/remotes/origin/main
  git merge --ff-only refs/remotes/origin/main
  python3 tools/validate_branch_policy.py --checkout
)
```

[`git merge --ff-only`](https://git-scm.com/docs/git-merge) refuses a divergent
history instead of silently making an integration commit. A refusal needs the
concurrent-work procedure below.

Keep each change cohesive and traceable to its roadmap phase. Review behavior,
edge cases, source evidence, licensing and honest capability descriptions. New
files require explicit provenance/inventory review. Stage only the reviewed
paths with `git add -- path/to/file`; never stage another contributor's work by
default. Inspect `git diff --cached --stat`, `git diff --cached` and
`git diff --cached --check`. Ask an independent reviewer to inspect the same
staged tree when available, and resolve findings before publication.

[Git's index](https://git-scm.com/docs/git-add) contains the selected content for
the next commit. Later edits to working files do not automatically update it.
[`git diff --cached`](https://git-scm.com/docs/git-diff) shows that staged change.
The checkout check deliberately rejects leftover unstaged or untracked source;
finish or separately preserve that work instead of deleting it to pass a check.

## Test the staged tree

Run the following from the repository root after staging. It records the parent
commit and staged tree, exports that tree, checks the export against Git objects,
then runs the full checks and real generic ARM64 build/smoke from the export.
Python, Git, a POSIX shell, `tar`, GNU Make, AArch64 GCC/binutils and QEMU must be
installed as described in the development guide. No download occurs here.

[`git write-tree`](https://git-scm.com/docs/git-write-tree) records the index as a
tree object without creating a commit or branch. The identity check matters:
[`git archive`](https://git-scm.com/docs/git-archive) can omit or transform files
through export attributes. A mismatched export is rejected before testing.

```sh
(
  set -eu
  python3 tools/validate_branch_policy.py --checkout
  git diff --cached --check
  p007_parent=$(git rev-parse HEAD)
  p007_tree=$(git write-tree)
  p007_tmp=$(mktemp -d)
  trap 'rm -rf "$p007_tmp"' EXIT
  trap 'exit 1' HUP INT TERM
  mkdir "$p007_tmp/source"
  git archive --format=tar --output="$p007_tmp/source.tar" "$p007_tree"
  tar -xf "$p007_tmp/source.tar" -C "$p007_tmp/source"
  python3 - "$p007_tree" "$p007_tmp/source" <<'PY'
import os
from pathlib import Path
import subprocess
import sys

tree, directory = sys.argv[1:]
root = Path(directory)
records = subprocess.check_output(
    ["git", "ls-tree", "-r", "-z", "--full-tree", tree]
).split(b"\0")
expected = set()
for record in filter(None, records):
    metadata, raw_path = record.split(b"\t", 1)
    mode, kind, object_id = metadata.decode("ascii").split()
    path = Path(os.fsdecode(raw_path))
    if kind != "blob" or mode not in {"100644", "100755"}:
        raise SystemExit("Export requires regular source files: " + str(path))
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit("Unsafe source path: " + str(path))
    exported = root / path
    if exported.is_symlink() or not exported.is_file():
        raise SystemExit("Missing or nonregular export: " + str(path))
    actual_id = subprocess.check_output(
        ["git", "hash-object", "--no-filters", str(exported)], text=True
    ).strip()
    executable = bool(exported.stat().st_mode & 0o111)
    if actual_id != object_id or executable != (mode == "100755"):
        raise SystemExit("Export differs from staged tree: " + str(path))
    expected.add(path.as_posix())
actual = {
    p.relative_to(root).as_posix() for p in root.rglob("*")
    if p.is_file() or p.is_symlink()
}
if actual != expected:
    raise SystemExit("Export path inventory differs from staged tree")
PY
  (
    cd "$p007_tmp/source"
    export PYTHONDONTWRITEBYTECODE=1
    python3 tools/validate_licensing.py --archive
    python3 tools/validate_target.py
    python3 tools/validate_fidelity.py
    python3 tools/validate_boot_milestone.py
    python3 tools/validate_scope.py
    python3 tools/validate_branch_policy.py
    python3 tools/validate_hardware.py
    python3 tools/validate_roadmap.py
    python3 -m unittest discover -s tests -v
    make -C experiments/arm64-virt-smoke
    python3 tools/run_arm64_smoke.py experiments/arm64-virt-smoke/build/hello.elf
  )
  test "$(git rev-parse HEAD)" = "$p007_parent"
  test "$(git write-tree)" = "$p007_tree"
  python3 tools/validate_branch_policy.py --checkout
  printf 'TESTED_PARENT=%s\nTESTED_TREE=%s\n' "$p007_parent" "$p007_tree"
)
```

Save the two final values with the test output. If any command fails, no verified
result was produced. A changed parent, index, source file, test or review finding
requires another review and verification pass. This example enforces the current
regular-file source boundary; third-party imports need their separate review.
The smoke output is evidence for generic QEMU `virt` with explicit TCG only.
It does not establish Apple CPU, T8103 Linux or macOS compatibility.

## Commit and publish

Use the two values printed by the successful run; do not replace them by freshly
reading the index. Replace the message with a concise description of your phase
and change. This block rechecks both identities, fetches the current remote tip,
commits the reviewed index, checks the resulting tree and publishes explicitly
to `main`.

```sh
(
  set -eu
  p007_tested_parent='PASTE_TESTED_PARENT'
  p007_tested_tree='PASTE_TESTED_TREE'
  python3 tools/validate_branch_policy.py --checkout
  test "$(git rev-parse HEAD)" = "$p007_tested_parent"
  test "$(git write-tree)" = "$p007_tested_tree"
  git fetch origin refs/heads/main:refs/remotes/origin/main
  git merge-base --is-ancestor refs/remotes/origin/main HEAD
  git commit -m "P007: establish the main contribution workflow"
  p007_commit=$(git rev-parse HEAD)
  test "$(git rev-parse "$p007_commit^")" = "$p007_tested_parent"
  test "$(git rev-parse "$p007_commit^{tree}")" = "$p007_tested_tree"
  python3 tools/validate_branch_policy.py --checkout
  git push origin "$p007_commit":refs/heads/main
  printf 'PUBLISHED_COMMIT=%s\n' "$p007_commit"
)
```

Use [`git commit`](https://git-scm.com/docs/git-commit) without automatic staging
or file arguments: those options can change what is committed after testing.
If a hook or concurrent operation changes the committed tree, the comparison
fails and publication stops. Preserve that local commit, inspect it and retest
before any push. The push uses the checked immutable commit ID, so a concurrent
change to local `HEAD` cannot silently change what is published. Recheck both
remote URLs if configuration changed during the work.
[`git push`](https://git-scm.com/docs/git-push) normally rejects
a non-fast-forward update; never override that safeguard.

In [GitHub Actions](https://github.com/cheshmakzanoon-ops/M1-apple-Emulator-v0.1/actions),
find the push run for the exact printed commit SHA. Check that both
`metadata-and-tests` and `arm64-toolchain-smoke` completed successfully, and
inspect their [job/step logs](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs).
Record the commit and run URL in the phase evidence. Pending, cancelled, skipped,
missing or failed required jobs are not a pass. A green run for an older commit
does not validate a newer one. Report an unavailable hosted check explicitly and
leave completion pending until the required evidence exists.

## Concurrent work and failures

If a fetch or push reveals new remote work, stop the publication sequence and
inspect both histories. A normal fast-forward update is safe only in a clean
checkout. If local and remote commits have diverged, preserve both histories and
coordinate a reviewed integration on the existing `main`; no auxiliary branch
is required. A merge can preserve both sets of commits, but its combined content
needs conflict review and the full checks again. Do not use force, discard work,
or rewrite published commits to make the push succeed. The normal checkout guard
rejects an active merge/rebase/cherry-pick; it cannot review or resolve one.

Fix a published regression with a new reviewed, tested commit, or a reviewed
revert that preserves history. Retry transient CI infrastructure failures against
the same SHA and report the new attempt; code fixes receive a new commit and a
new run. Do not check a phase complete merely because publication succeeded.

This policy and its local checks do not configure server-side enforcement.
GitHub's [required pull-request reviews](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
require collaborators to use approved PRs and are not a prerequisite for this
workflow. Existing access controls still apply. Do not weaken or bypass them;
report an incompatible repository rule for owner resolution. Hosted checks
triggered by a push run after publication, so they are evidence for that commit,
not a claim that the server prevented all untested pushes.
