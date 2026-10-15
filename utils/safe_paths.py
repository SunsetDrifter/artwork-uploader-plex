"""
Keep a file name from the client inside the folder it is meant for (homelab fork hardening).

os.path.join(base, name) drops base when name is absolute and walks out of it on "../", so
a name taken from a socket event must be checked before it reaches open(), os.remove() or
shutil.move(). The app runs as root in its container, so an unchecked name is a read, write
or delete of any file in it.
"""

import os


class UnsafePathError(ValueError):
    """Raised when a client supplied file name would resolve outside its base folder."""


def safe_child_path(base_dir: str, name) -> str:
    """Return the resolved path of name directly inside base_dir, or raise UnsafePathError.

    Only a bare file name is accepted: no separators, no "." or "..", no leading dot, no NUL.
    The resolved path (symlinks followed) must still sit directly inside base_dir.
    """
    if not isinstance(name, str) or not name or "\x00" in name:
        raise UnsafePathError("Invalid file name")
    if "/" in name or "\\" in name or name.startswith("."):
        raise UnsafePathError(f"Invalid file name: {name!r}")

    base = os.path.realpath(base_dir)
    path = os.path.realpath(os.path.join(base, name))
    if os.path.dirname(path) != base:
        raise UnsafePathError(f"Invalid file name: {name!r}")
    return path
