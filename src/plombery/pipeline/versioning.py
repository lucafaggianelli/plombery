import subprocess
from functools import cache
from pathlib import Path

_GIT_DESCRIBE = ("git", "describe", "--tags", "--always", "--dirty")


@cache
def get_version_from_git(directory: str) -> str | None:
    """The revision of the git repository containing `directory`, if any.

    Returns `None` whenever the answer isn't trustworthy — no repository (the
    usual case in a container, where the code is copied without its history),
    no `git` executable, an empty repository — so that the caller can fall
    back to something else.

    Cached per directory: the code being run can't change while the process
    is alive, and a run must not pay for a subprocess.
    """

    repository = _find_repository(Path(directory))

    if not repository:
        return None

    try:
        result = subprocess.run(
            _GIT_DESCRIBE,
            cwd=repository,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    return result.stdout.strip() or None


def _find_repository(directory: Path) -> str | None:
    """The closest ancestor of `directory` holding a `.git`, itself included.

    `.git` is a directory in a plain clone and a file in a worktree or a
    submodule, so its mere existence is what's checked.
    """

    try:
        directory = directory.resolve()
    except OSError:
        return None

    for candidate in (directory, *directory.parents):
        if (candidate / ".git").exists():
            return str(candidate)

    return None
