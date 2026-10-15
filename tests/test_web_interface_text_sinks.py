"""
Homelab fork: log lines, status messages and run labels reach the page as text.

Log and status messages carry scraped poster titles, ThePosterDB set authors, uploaded ZIP
names and the Title:/Author: lines of a ZIP's source.txt, all of which are outside input.
Neither the server nor the page ever sends markup through them, so they are written with
textContent. Like test_web_interface_escaping.py this reads the shipped script, because
there is no JavaScript test runner here.
"""

import os
import re

import pytest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "static", "web_interface.js")


@pytest.fixture(scope="module")
def script():
    with open(SCRIPT, encoding="utf-8") as handle:
        return handle.read()


def _function_body(script, name):
    start = script.index(f"function {name}(")
    end = script.index("\nfunction ", start + 1)
    return script[start:end]


@pytest.mark.unit
@pytest.mark.parametrize("name", ["updateLog", "updateStatus"])
def test_messages_are_written_as_text(script, name):
    body = _function_body(script, name)

    assert ".innerHTML = message" not in body
    assert ".textContent = message" in body


@pytest.mark.unit
def test_the_run_log_button_does_not_splice_the_label_into_script(script):
    assert "'${run.label}'" not in script
    assert "'${logFileName}'" not in script


@pytest.mark.unit
def test_inline_handler_arguments_are_json_and_attribute_escaped(script):
    body = _function_body(script, "jsCallArgs")

    assert "JSON.stringify" in body
    assert re.search(r"&quot;", body)
