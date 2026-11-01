#!/usr/bin/env python3
"""Rehearse a local upstream revision in a disposable repository; never commit/push."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def git(repo, *args, check=True, binary=False):
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgSign=false",
         "-c", "rerere.enabled=false", "-C", str(repo), *args],
        capture_output=True, text=not binary, check=check, timeout=120,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def snapshot(repo):
    """Read the effective working tree, including staged+unstaged and nonignored new files."""
    patch = git(repo, "diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", "HEAD", binary=True).stdout
    names = git(repo, "ls-files", "--others", "--exclude-standard", "-z", binary=True).stdout.split(b"\0")
    new = {}
    for raw in names:
        if not raw:
            continue
        name = os.fsdecode(raw)
        path = repo / name
        if path.is_symlink():
            value = {"symlink": os.readlink(path)}
        else:
            value = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mode": path.stat().st_mode & 0o777}
        new[name] = value
    return patch, new


def include_snapshot(repo, sandbox, evidence):
    patch, new = snapshot(repo)
    patch_path = evidence / "fork-working-tree.patch"
    patch_path.write_bytes(patch)
    if patch:
        git(sandbox, "apply", "--index", "--binary", str(patch_path))
    for name in new:
        source, target = repo / name, sandbox / name
        if sandbox.resolve() not in target.parent.resolve().parents and target.parent.resolve() != sandbox.resolve():
            raise ValueError(f"unsafe snapshot destination: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=False)
        retained = evidence / "fork-untracked" / name
        retained.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, retained, follow_symlinks=False)
    if snapshot(repo) != (patch, new):
        raise ValueError("working tree changed while being copied; retry once editing has stopped")
    git(sandbox, "add", "--all")
    tree = git(sandbox, "write-tree").stdout.strip()
    (evidence / "fork-untracked.json").write_text(json.dumps(new, indent=2) + "\n")
    return {"tree": tree, "trackedPatchSha256": hashlib.sha256(patch).hexdigest(), "untrackedFiles": new}


def save_conflicts(sandbox, evidence, conflicts):
    for name in conflicts:
        target = evidence / "conflicts" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        working = sandbox / name
        if working.is_file() and not working.is_symlink():
            shutil.copy2(working, target)
        # Preserve all available base/ours/theirs blobs, including delete/modify conflicts.
        for stage in (1, 2, 3):
            blob = git(sandbox, "show", f":{stage}:{name}", check=False, binary=True)
            if blob.returncode == 0:
                target.with_name(target.name + f".stage{stage}").write_bytes(blob.stdout)


def tree_entries(repo, tree):
    entries = {}
    for line in git(repo, "ls-tree", "-r", "-z", tree, binary=True).stdout.split(b"\0"):
        if line:
            metadata, name = line.split(b"\t", 1)
            entries[os.fsdecode(name)] = metadata.decode().split()
    return entries


def structural_conflicts(sandbox, base, ours, theirs, evidence):
    trees = [tree_entries(sandbox, tree) for tree in (base, ours, theirs)]
    conflicts = []
    for name in sorted(set().union(*trees)):
        old, local, incoming = [tree.get(name) for tree in trees]
        if incoming == old or local == old or local == incoming:
            continue
        kind = None
        if old and local is None and incoming:
            kind = "fork-deleted/upstream-modified"
        elif old and incoming is None and local:
            kind = "fork-modified/upstream-deleted"
        elif old is None and local and incoming:
            kind = "add/add"
        if kind:
            conflicts.append({"path": name, "kind": kind})
            target = evidence / "conflicts" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            for index, entry in enumerate((old, local, incoming), 1):
                if entry and entry[1] == "blob":
                    target.with_name(target.name + f".stage{index}").write_bytes(git(sandbox, "cat-file", "blob", entry[2], binary=True).stdout)
    return conflicts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", help="already-fetched, reviewed local upstream ref or SHA")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path, required=True, help="new JSON file outside source checkout")
    parser.add_argument("--include-working-tree", action="store_true", help="snapshot dirty files; rehearse a three-way upstream patch without creating commits")
    parser.add_argument("--candidate-source", help="explicit Git source URL/path; fetch candidate only into disposable repository")
    args = parser.parse_args()
    repo = Path(git(args.repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    report = args.report.resolve()
    if repo == report or repo in report.parents:
        parser.error("report must be outside the source checkout")
    if report.exists():
        parser.error("report already exists; refusing to overwrite")
    if not args.include_working_tree and git(repo, "status", "--porcelain", "--untracked-files=all").stdout:
        parser.error("source checkout is dirty; finish review/commit through the normal workflow first")
    head = git(repo, "rev-parse", "HEAD^{commit}").stdout.strip()
    index = Path(git(repo, "rev-parse", "--git-path", "index").stdout.strip())
    if not index.is_absolute():
        index = repo / index
    original_index = hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None
    candidate = None if args.candidate_source else git(repo, "rev-parse", "--verify", "--end-of-options", args.candidate + "^{commit}").stdout.strip()
    evidence = report.with_suffix(".evidence")
    evidence.mkdir(parents=False, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="omagrid-merge-") as temporary:
        sandbox = Path(temporary)
        git(sandbox, "init", "--quiet")
        # Local fetch only, detached checkout only in this disposable repository.
        git(sandbox, "fetch", "--quiet", "--no-tags", str(repo), head)
        if args.candidate_source:
            git(sandbox, "fetch", "--quiet", "--no-tags", args.candidate_source, args.candidate)
            candidate = git(sandbox, "rev-parse", "FETCH_HEAD^{commit}").stdout.strip()
        else:
            git(sandbox, "fetch", "--quiet", "--no-tags", str(repo), candidate)
        base = git(sandbox, "merge-base", head, candidate).stdout.strip()
        git(sandbox, "checkout", "--quiet", "--detach", head)
        source_snapshot = None
        structural = []
        if args.include_working_tree:
            source_snapshot = include_snapshot(repo, sandbox, evidence)
            structural = structural_conflicts(sandbox, base, source_snapshot["tree"], candidate, evidence)
            patch = git(sandbox, "diff", "--binary", "--full-index", "--no-renames", "--no-ext-diff", "--no-textconv", base, candidate, binary=True).stdout
            patch_path = evidence / "upstream.patch"
            patch_path.write_bytes(patch)
            if not patch:
                raise ValueError("candidate has no change from merge base; this is not a divergent integration rehearsal")
            excluded = [f"--exclude={item['path']}" for item in structural]
            merged = git(sandbox, "apply", "--3way", "--index", "--binary", *excluded, str(patch_path), check=False)
        else:
            merged = git(sandbox, "-c", "user.name=Merge rehearsal", "-c", "user.email=rehearsal@invalid",
                         "merge", "--no-commit", "--no-ff", "--no-edit", "--no-gpg-sign", candidate, check=False)
        conflicts = git(sandbox, "diff", "--name-only", "--diff-filter=U").stdout.splitlines()
        save_conflicts(sandbox, evidence, conflicts)
        conflicts = sorted(set(conflicts).union(item["path"] for item in structural))
        (evidence / "index-status.txt").write_text(git(sandbox, "status", "--short").stdout)
        (evidence / "integration.stdout").write_text(merged.stdout)
        (evidence / "integration.stderr").write_text(merged.stderr)
        index_after = hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None
        unchanged = head == git(repo, "rev-parse", "HEAD^{commit}").stdout.strip() and original_index == index_after
        if not unchanged:
            raise ValueError("source HEAD/index changed during rehearsal; report refused")
        result = {"head": head, "candidate": candidate, "mergeBase": base,
                  "method": "three-way-patch" if args.include_working_tree else "git-merge-no-commit",
                  "candidateSource": args.candidate_source or "local repository",
                  "forkSnapshot": source_snapshot, "evidence": str(evidence),
                  "upstreamChangedFiles": git(sandbox, "diff", "--name-only", base, candidate).stdout.splitlines(),
                  "upstreamCommits": int(git(sandbox, "rev-list", "--count", base + ".." + candidate).stdout),
                  "structuralConflicts": structural,
                  "sourceHeadAndIndexUnchanged": unchanged,
                  "sourceIndexSha256": original_index,
                  "status": "conflict" if conflicts else "clean" if merged.returncode == 0 else "error",
                  "exitCode": merged.returncode, "conflicts": conflicts,
                  "stdout": merged.stdout, "stderr": merged.stderr,
                  "testsRun": False, "committed": False, "pushed": False}
        with report.open("x") as output:
            json.dump(result, output, indent=2)
            output.write("\n")
    print(f"{result['status']}: {report}")
    return 0 if result["status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
