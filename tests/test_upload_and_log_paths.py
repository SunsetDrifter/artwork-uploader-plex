"""
Homelab fork: the upload file name and the log file name from the browser stay in their folders.

save_uploaded_file moved the uploaded archive to os.path.join(temp_folder, file_name), so a
file name of "/usr/local/lib/python3.14/site-packages/x.pth" planted arbitrary bytes there as
root. get_log_file read os.path.join("logs", name) and sent the contents back, so
"../config/config.json" returned the Plex token.
"""

import os
import tempfile

import pytest

import artwork_uploader
import core.globals as app_globals
import web_routes
from models.instance import Instance


class _NullRunHistory:
    def add_run(self, **kwargs):
        return None


@pytest.fixture
def upload(tmp_path, monkeypatch):
    """Drives save_uploaded_file with extraction stubbed, recording where the archive landed."""
    created, landed = [], []
    real_mkdtemp = tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    def extract(instance, zip_path, extract_dir, *args, **kwargs):
        landed.append(zip_path)
        return [], 0, "", "", ""

    monkeypatch.setattr(web_routes.tempfile, "mkdtemp", recording_mkdtemp)
    monkeypatch.setattr(web_routes, "update_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(web_routes, "update_status", lambda *args, **kwargs: None)
    monkeypatch.setattr(web_routes, "notify_web", lambda *args, **kwargs: None)
    monkeypatch.setattr(web_routes, "RunHistory", lambda: _NullRunHistory())
    monkeypatch.setattr(web_routes, "extract_and_list_zip", extract)
    monkeypatch.setattr(app_globals, "cancel_scrape", False)
    monkeypatch.setattr(app_globals, "scrapes_running", 1)
    monkeypatch.setattr(artwork_uploader, "process_uploaded_artwork", lambda *args, **kwargs: None)

    def run(file_name):
        source = tmp_path / "chunked-upload"
        source.write_bytes(b"not really a zip")
        web_routes.save_uploaded_file(
            Instance(broadcast=True), file_name, [], [], "", None,
            {file_name: {"temp_path": str(source)}},
            web_routes.re.compile(r".*"), lambda path: "portrait", lambda artwork: 0,
        )

    return run, created, landed


@pytest.mark.unit
def test_an_absolute_upload_name_lands_in_the_temp_folder(upload, tmp_path):
    run, created, landed = upload
    planted = tmp_path / "site-packages" / "evil.pth"
    planted.parent.mkdir()

    run(str(planted))

    assert not planted.exists()
    assert os.path.dirname(landed[0]) == created[0]
    assert os.path.basename(landed[0]) == "evil.pth"


@pytest.mark.unit
def test_a_traversing_upload_name_lands_in_the_temp_folder(upload):
    run, created, landed = upload

    run("../../escaped.zip")

    assert os.path.dirname(landed[0]) == created[0]


@pytest.mark.unit
def test_a_normal_upload_name_keeps_its_name(upload):
    run, created, landed = upload

    run("Dune (2021) set by someone.zip")

    assert landed[0] == os.path.join(created[0], "Dune (2021) set by someone.zip")


def _log_reply(web_harness, name):
    client = web_harness.socket_client()
    client.emit("get_log_file", {"instance_id": "abc", "log_file_name": name})
    replies = [m for m in client.get_received() if m["name"] == "get_log_file"]
    assert replies, "get_log_file sent nothing back"
    return replies[0]["args"][0]


@pytest.mark.unit
def test_a_log_file_in_logs_is_returned(web_harness, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "run.log").write_text("a run log")

    reply = _log_reply(web_harness, "run.log")

    assert reply["success"] is True
    assert reply["contents"] == "a run log"


@pytest.mark.unit
@pytest.mark.parametrize("name", ["../secret.txt", "SECRET_ABSOLUTE"])
def test_a_log_name_outside_logs_returns_nothing(web_harness, tmp_path, monkeypatch, name):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("plex token")
    if name == "SECRET_ABSOLUTE":
        name = str(secret)

    reply = _log_reply(web_harness, name)

    assert reply["success"] is False
    assert reply["contents"] == ""
