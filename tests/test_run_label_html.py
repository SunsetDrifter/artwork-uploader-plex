"""
Homelab fork: a run label is text, never markup or script, in the run history table.

Run labels are a scraped URL, an uploaded ZIP's file name, or a webhook title. They used to
be spliced raw into an <a href>, title attributes, a <span>, and an inline onclick string,
so a ZIP named `x<img src=x onerror=...>.zip` ran script every time the History tab opened,
and any label merely containing "https" became a link, including `javascript:...//https`.
"""

import html
import json
import re

import pytest

from utils.run_label_html import build_run_label_html

TIMESTAMP = "2026-10-15T14:52:12+00:00"
PAYLOADS = [
    "Dune (2021) <img src=x onerror=alert(1)>",
    "x'); alert(1); ('",
    'x"); alert(1); ("',
    "</span><script>alert(1)</script>",
]


def _onclick_args(markup):
    """The JS the browser runs for the delete button: unescape the attribute, return its args."""
    match = re.search(r'onclick="deleteRun\((.*)\)"', markup)
    assert match, "delete button lost its onclick"
    return json.loads("[" + html.unescape(match.group(1)) + "]")


@pytest.mark.unit
@pytest.mark.parametrize("label", PAYLOADS)
def test_a_hostile_label_is_escaped_text(label):
    markup = build_run_label_html(label, TIMESTAMP)

    assert "<img" not in markup
    assert "<script" not in markup
    assert html.escape(label, quote=True) in markup


@pytest.mark.unit
@pytest.mark.parametrize("label", PAYLOADS + ["https://theposterdb.com/set/123"])
def test_the_delete_button_receives_the_label_as_one_string(label):
    assert _onclick_args(build_run_label_html(label, TIMESTAMP)) == [TIMESTAMP, label]


@pytest.mark.unit
def test_a_url_label_becomes_a_link_to_that_url():
    markup = build_run_label_html("https://theposterdb.com/set/123", TIMESTAMP)

    assert "href='https://theposterdb.com/set/123'" in markup
    assert ">123</span>" in markup


@pytest.mark.unit
@pytest.mark.parametrize("label", [
    "javascript:alert(1)//https://x/y/z",
    "data:text/html,<script>alert(1)</script>//https",
    "http://theposterdb.com/set/1?https",
])
def test_a_label_that_only_mentions_https_is_never_a_link(label):
    markup = build_run_label_html(label, TIMESTAMP)

    assert "href=" not in markup
    assert "<script" not in markup


@pytest.mark.unit
def test_a_url_with_markup_in_its_path_is_escaped():
    markup = build_run_label_html("https://theposterdb.com/set/<b>1</b>'onmouseover='alert(1)", TIMESTAMP)

    assert "<b>" not in markup
    assert "'onmouseover='" not in markup


@pytest.mark.unit
def test_an_empty_label_has_no_markup():
    assert build_run_label_html("", TIMESTAMP) is None
