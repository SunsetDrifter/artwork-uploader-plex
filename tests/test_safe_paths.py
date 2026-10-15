"""
Homelab fork: a file name from the browser never leaves the folder it names.

The socket handlers for bulk import files, run log files and uploaded archives join a name
from the client onto a base folder. os.path.join drops the base when the name is absolute,
and "../" walks out of it, so before this a signed-in page could read, write, rename or
delete any file in the container as root, including a .pth file under site-packages that
the next python start runs. safe_child_path is the one check they all go through.
"""

import os

import pytest

from utils.safe_paths import UnsafePathError, safe_child_path


@pytest.mark.unit
def test_a_plain_name_resolves_inside_the_base(tmp_path):
    assert safe_child_path(str(tmp_path), "bulk_import.txt") == os.path.join(os.path.realpath(tmp_path), "bulk_import.txt")


@pytest.mark.unit
@pytest.mark.parametrize("name", [
    "/usr/local/lib/python3.14/site-packages/zz.pth",
    "../config/config.json",
    "../../etc/passwd",
    "sub/file.txt",
    "sub\\file.txt",
    "..",
    ".",
    "",
    ".hidden",
    "nul\x00byte.txt",
    None,
    42,
])
def test_a_name_that_could_leave_the_base_is_refused(tmp_path, name):
    with pytest.raises(UnsafePathError):
        safe_child_path(str(tmp_path), name)


@pytest.mark.unit
def test_a_symlink_out_of_the_base_is_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    base = tmp_path / "base"
    base.mkdir()
    (base / "link.txt").symlink_to(outside / "target.txt")

    with pytest.raises(UnsafePathError):
        safe_child_path(str(base), "link.txt")
