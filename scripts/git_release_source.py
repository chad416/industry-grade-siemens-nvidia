"""Read controlled release bytes from Git HEAD, the index, or the worktree."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GitReleaseError(RuntimeError):
    """Raised when an authoritative Git byte source cannot be read."""


def _git(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitReleaseError(f"git {' '.join(args)} failed ({result.returncode}): {detail}")
    return result.stdout


def _zpaths(payload: bytes) -> list[str]:
    return [item.decode("utf-8", errors="strict") for item in payload.split(b"\0") if item]


def tracked_paths(source: str) -> list[str]:
    if source == "head":
        return sorted(_zpaths(_git("ls-tree", "-r", "-z", "--name-only", "HEAD")))
    if source == "index":
        return sorted(_zpaths(_git("ls-files", "-z")))
    if source == "worktree":
        return sorted(
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(ROOT).parts
        )
    raise ValueError(f"Unsupported byte source: {source}")


def read_bytes(source: str, rel: str) -> bytes:
    if source == "head":
        return _git("show", f"HEAD:{rel}")
    if source == "index":
        return _git("show", f":{rel}")
    if source == "worktree":
        return (ROOT / rel).read_bytes()
    raise ValueError(f"Unsupported byte source: {source}")


def untracked_paths() -> list[str]:
    return sorted(_zpaths(_git("ls-files", "-z", "--others", "--exclude-standard")))


def unstaged_paths() -> list[str]:
    return sorted(_zpaths(_git("diff", "--name-only", "-z")))


def staged_paths() -> list[str]:
    return sorted(_zpaths(_git("diff", "--cached", "--name-only", "-z")))


def head_sha() -> str:
    return _git("rev-parse", "HEAD").decode("ascii").strip()


def assert_index_inputs_staged(*, allow_unstaged: set[str] | None = None) -> None:
    allowed = allow_unstaged or set()
    unstaged = [path for path in unstaged_paths() if path not in allowed]
    untracked = untracked_paths()
    if unstaged or untracked:
        details = []
        if unstaged:
            details.append(f"unstaged={unstaged}")
        if untracked:
            details.append(f"untracked={untracked}")
        raise GitReleaseError("Index is not the complete candidate release: " + "; ".join(details))


def clean_state_errors() -> list[str]:
    errors = []
    for label, paths in (
        ("staged change", staged_paths()),
        ("unstaged change", unstaged_paths()),
        ("untracked path", untracked_paths()),
    ):
        errors.extend(f"{label}: {path}" for path in paths)
    return errors
