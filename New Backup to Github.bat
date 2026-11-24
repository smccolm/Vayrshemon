@python -x "%~f0" %* & @exit /b
# Windows entry point above. The rest runs with the standard Python 3 library.
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

EDITION = "Saves/Vayrshemon Dictionary - Four-Column Progressive Edition/"
ASSETS = (
    EDITION + "Vayrshemon Dictionary - Four-Column Progressive Edition.vay",
    "Saves/Vayrshemon Dictionary - Letter Print Edition/Reciprocal vocabulary/"
    "Vayrshemon Dictionary and Thesaurus - Complete Duplex Print.pdf",
)
DB = EDITION + "Working/corpus.sqlite3"
LOCAL_FILES = tuple(DB + suffix for suffix in ("", "-wal", "-shm", "-journal"))
METADATA = (".gitignore", ".gitattributes")
LIMIT = 100 * 1024 * 1024


def git(repo, *args, data=None, env=None):
    proc = subprocess.run(["git", *args], cwd=repo, input=data, stdout=subprocess.PIPE, env=env)
    if proc.returncode:
        raise RuntimeError("Git command failed: git " + args[0])
    return proc.stdout


def value(repo, *args):
    return os.fsdecode(git(repo, *args).rstrip(b"\r\n"))


def paths(data):
    return {os.fsdecode(p) for p in data.split(b"\0") if p}


def check_checkout(repo, head):
    if value(repo, "symbolic-ref", "--short", "HEAD") != "main" or value(repo, "rev-parse", "HEAD") != head:
        raise RuntimeError("Run this repair on main. Its tip must stay fixed during the repair.")
    git_dir = Path(value(repo, "rev-parse", "--absolute-git-dir"))
    if any((git_dir / p).exists() for p in ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "sequencer", "index.lock")):
        raise RuntimeError("Finish the current Git operation before running the repair.")
    if git(repo, "diff", "--cached", "--name-only", "-z") or paths(git(repo, "diff", "--name-only", "-z")) - set(LOCAL_FILES):
        raise RuntimeError("Commit or stash outstanding tracked changes first. Working database edits can stay in place.")
    tracked_meta = paths(git(repo, "ls-files", "-z", "--", *METADATA))
    for name in METADATA:
        if (repo / name).is_symlink() or ((repo / name).exists() and name not in tracked_meta):
            raise RuntimeError("Save and commit the repository's " + name + " before retrying.")
    if not all((repo / name).is_file() for name in (*ASSETS, DB)):
        raise RuntimeError("A dictionary, PDF or database path from the rejection is missing on disk.")


def append_ignores(work):
    path = work / ".gitignore"
    old = path.read_bytes() if path.exists() else b""
    lines = [("/" + name).encode("ascii") for name in LOCAL_FILES]
    # Append at the end so these exact rules take precedence over earlier negations.
    nl = b"\r\n" if b"\r\n" in old else b"\n"
    if old.splitlines()[-len(lines):] == lines:
        return
    with path.open("ab") as stream:
        if old and not old.endswith(b"\n"):
            stream.write(nl)
        stream.write(nl.join(lines) + nl)


def repair(repo):
    repo = Path(value(repo, "rev-parse", "--show-toplevel"))
    head = value(repo, "rev-parse", "HEAD")
    check_checkout(repo, head)
    git(repo, "lfs", "install", "--local")
    git(repo, "fetch", "--no-tags", "origin", "refs/heads/main:refs/remotes/origin/main")
    base = value(repo, "rev-parse", "refs/remotes/origin/main")
    git(repo, "merge-base", "--is-ancestor", base, head)
    if base == head:
        print("Local main and origin/main are already at the same commit.")
        return
    count = value(repo, "rev-list", "--count", base + ".." + head)
    print("Repairing " + count + " unpublished main commit(s) in a temporary local clone.", flush=True)
    envlines = value(repo, "lfs", "env").splitlines()
    media = next(line.partition("=")[2] for line in envlines if line.startswith("LocalMediaDir="))
    storage = Path(media).resolve().parent
    backup = "backup/vayrshemon-before-size-repair-" + head[:12]
    git_dir = Path(value(repo, "rev-parse", "--absolute-git-dir"))
    with tempfile.TemporaryDirectory(prefix="vayrshemon-repair-", dir=git_dir) as temp:
        work = Path(temp) / "work"
        skip = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1", FILTER_BRANCH_SQUELCH_WARNING="1")
        git(repo, "clone", "--shared", "--single-branch", "--branch", "main", "--no-checkout", "--", str(repo), str(work), env=skip)
        # Use the owner's commit identity and retain new LFS objects in their local store.
        for key in ("user.name", "user.email"):
            git(work, "config", "--local", key, value(repo, "config", "--get", key))
        git(work, "config", "--local", "lfs.storage", str(storage))
        git(work, "lfs", "install", "--local")
        git(work, "reset", "--hard", "HEAD", env=skip)
        git(work, "update-ref", "refs/repair/published", base)
        index_filter = "git rm -q --cached --ignore-unmatch -- " + " ".join(map(shlex.quote, LOCAL_FILES))
        git(work, "filter-branch", "--index-filter", index_filter, "--", "main", "^" + base, env=skip)
        git(work, "lfs", "migrate", "import", "--include-ref=refs/heads/main",
            "--exclude-ref=refs/repair/published", "--include=" + ",".join(ASSETS), env=skip)
        append_ignores(work)
        git(work, "add", "--", ".gitignore")
        if git(work, "diff", "--cached", "--name-only", "-z"):
            git(work, "commit", "--amend", "--no-edit", "--allow-empty", "--no-gpg-sign")
        fixed = value(work, "rev-parse", "HEAD")
        git(work, "merge-base", "--is-ancestor", base, fixed)
        if value(work, "rev-list", "--count", base + ".." + fixed) != count:
            raise RuntimeError("The pending commit count changed during repair.")
        changed = paths(git(work, "diff", "--no-renames", "--name-only", "-z", head, fixed))
        if changed - set((*ASSETS, *LOCAL_FILES, *METADATA)):
            raise RuntimeError("The candidate repair changed an unexpected path.")
        for name in ASSETS:
            if int(value(work, "cat-file", "-s", "HEAD:" + name)) > 1024:
                raise RuntimeError("Missing LFS pointer for " + name)
            pointer = git(work, "show", "HEAD:" + name)
            verified = git(repo, "lfs", "pointer", "--file=" + str(repo / name))
            if pointer.splitlines() != verified.splitlines():
                raise RuntimeError("LFS content does not match the local file: " + name)
        for name in LOCAL_FILES:
            git(work, "check-ignore", "-q", "--", name)
        ids = git(work, "rev-list", "--objects", "--no-object-names", base + ".." + fixed)
        sizes = git(work, "cat-file", "--batch-check=%(objecttype) %(objectsize)", data=ids)
        if any(int(n) > LIMIT for kind, n in (line.split() for line in sizes.splitlines()) if kind == b"blob"):
            raise RuntimeError("Another pending file exceeds 100 MiB. The original branch is still in place.")
        # Validate every candidate tree, including small database versions in earlier commits.
        for commit in value(work, "rev-list", base + ".." + fixed).splitlines():
            if git(work, "ls-tree", "-r", "--name-only", "-z", commit, "--", *LOCAL_FILES):
                raise RuntimeError("A local database file remains in pending commit " + commit)
        check_checkout(repo, head)
        if fixed == head:
            print("The pending commits already pass the size and tracking checks. Run the normal push.")
            return
        git(repo, "fetch", "--no-tags", str(work), "refs/heads/main")
        if value(repo, "rev-parse", "FETCH_HEAD") != fixed:
            raise RuntimeError("The candidate commit could not be verified after transfer.")
        # Only the two metadata files are checked out in the real working directory.
        existing_backup = value(repo, "for-each-ref", "--format=%(objectname)", "refs/heads/" + backup)
        if not existing_backup:
            git(repo, "branch", backup, head)
        elif existing_backup != head:
            raise RuntimeError("An existing recovery branch with this name points to another commit.")
        print("Local recovery branch: " + backup, flush=True)
        git(repo, "update-ref", "-m", "repair rejected Vayrshemon push", "refs/heads/main", fixed, head)
        git(repo, "reset", "--mixed", "HEAD")
        git(repo, "restore", "--source=HEAD", "--worktree", "--", *METADATA)
    for name in LOCAL_FILES:
        git(repo, "check-ignore", "-q", "--", name)
    if paths(git(repo, "diff", "--name-only", "-z")):
        raise RuntimeError("Review git status before pushing. The recovery branch preserves the original commits.")
    print("Repair complete. Run your existing push_to_github.bat to publish main.")


if __name__ == "__main__":
    try:
        repair(Path(sys.argv[1] if len(sys.argv) > 1 else r"E:\Vayrshemon").resolve())
    except (OSError, RuntimeError) as error:
        print("Stopped: " + str(error), file=sys.stderr)
        sys.exit(1)
