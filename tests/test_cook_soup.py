"""Unit tests for cook_soup (utils/soup_utils.py)."""

import pytest

from core.exceptions import ScraperException
from utils.soup_utils import cook_soup


@pytest.mark.unit
def test_an_existing_local_html_file_is_refused(tmp_path):
    # Homelab fork: the local-file read upstream supports is an arbitrary file read
    # from a caller-supplied path, so it is removed and must fail closed.
    page = tmp_path / "poster_page.html"
    page.write_text("<html><body><h1>Poster set</h1></body></html>", encoding="utf-8")

    with pytest.raises(ScraperException) as raised:
        cook_soup(str(page))

    assert "poster_page.html" in str(raised.value)


@pytest.mark.unit
def test_a_path_that_is_neither_a_url_nor_html_is_refused(tmp_path):
    with pytest.raises(ScraperException) as raised:
        cook_soup(str(tmp_path / "notes.txt"))

    assert "notes.txt" in str(raised.value)


@pytest.mark.unit
def test_a_missing_html_file_is_refused(tmp_path):
    with pytest.raises(ScraperException) as raised:
        cook_soup(str(tmp_path / "gone.html"))

    assert "gone.html" in str(raised.value)
