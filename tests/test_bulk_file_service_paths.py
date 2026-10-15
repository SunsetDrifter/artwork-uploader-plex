"""Homelab fork: every bulk import file operation stays inside bulk_imports/."""

import os

import pytest

from services.bulk_file_service import BulkFileService
from utils.safe_paths import UnsafePathError

ESCAPES = ["/tmp/escape.txt", "../escape.txt", "../../escape.pth"]


@pytest.fixture
def service(tmp_path):
    (tmp_path / "bulk_imports").mkdir()
    return BulkFileService(str(tmp_path))


@pytest.mark.unit
def test_a_normal_file_round_trips(service, tmp_path):
    service.write_file("https://theposterdb.com/set/1\n", "mine.txt")
    assert service.read_file("mine.txt") == "https://theposterdb.com/set/1\n"
    assert (tmp_path / "bulk_imports" / "mine.txt").exists()


@pytest.mark.unit
def test_the_default_name_still_works(service):
    service.ensure_default_file_exists()
    assert service.file_exists()


@pytest.mark.unit
@pytest.mark.parametrize("name", ESCAPES)
def test_write_refuses_a_path_outside_bulk_imports(service, tmp_path, name):
    with pytest.raises(UnsafePathError):
        service.write_file("import os\n", name)
    assert not (tmp_path / "escape.txt").exists()


@pytest.mark.unit
@pytest.mark.parametrize("name", ESCAPES)
def test_read_delete_and_exists_refuse_a_path_outside_bulk_imports(service, tmp_path, name):
    (tmp_path / "escape.txt").write_text("secret")
    with pytest.raises(UnsafePathError):
        service.read_file(name)
    with pytest.raises(UnsafePathError):
        service.delete_file(name)
    with pytest.raises(UnsafePathError):
        service.file_exists(name)
    assert (tmp_path / "escape.txt").exists()


@pytest.mark.unit
def test_rename_refuses_either_side_outside_bulk_imports(service, tmp_path):
    service.write_file("x\n", "a.txt")
    with pytest.raises(UnsafePathError):
        service.rename_file("a.txt", "../moved.txt")
    with pytest.raises(UnsafePathError):
        service.rename_file("../../config/config.json", "b.txt")
    assert os.path.exists(tmp_path / "bulk_imports" / "a.txt")
