"""
Build the run history label cell (homelab fork hardening).

The label is outside input (a scraped URL, an uploaded ZIP's name, a webhook title), and the
table writes this markup with innerHTML. Every value is HTML-escaped; the arguments of the
inline delete handler are JSON-encoded first and then attribute-escaped, because the browser
decodes the attribute before it parses the JavaScript. Only a label that starts with https://
becomes a link, so a "javascript:" label can never be one.
"""

import html
import json
from typing import Optional

from core.constants import URL_SOURCE_MAP, URL_TYPE_MAP

_UNKNOWN_TYPE = {"icon": "question-circle", "label": "Unknown URL type"}


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _delete_button(timestamp: str, label: str) -> str:
    args = _esc(f"{json.dumps(timestamp)}, {json.dumps(label)}")
    return (
        "<i class='bi bi-trash3 inline-run-btn text-danger cursor-pointer' "
        "style='cursor: pointer; font-size: 0.8rem;' title='Delete run' "
        f'onclick="deleteRun({args})"></i>'
    )


def build_run_label_html(label: str, timestamp: str) -> Optional[str]:
    """Return the label cell markup for one run, or None when the run has no label."""
    if not label:
        return None
    delete_button = _delete_button(timestamp, label)

    if label.startswith("https://"):
        parts = [p for p in label[len("https://"):].strip().split("/") if p]
        if len(parts) < 3:
            return f"<i class='bi bi-x-octagon text-danger' title='{_esc(label)}'>&nbsp;Error parsing URL</i>"
        domain, asset_type, asset_id = parts[0], parts[1], parts[2]
        source = URL_SOURCE_MAP.get(domain, "Unknown")
        url_type = URL_TYPE_MAP.get(asset_type, _UNKNOWN_TYPE)
        return (
            f"<a href='{_esc(label)}' target='_blank' rel='noopener noreferrer' "
            f"class='text-decoration-none text-reset' title='{_esc(label)}'>{_esc(source)} "
            f"<i class='bi bi-{_esc(url_type.get('icon', 'question-circle'))}' "
            f"title='{_esc(url_type.get('label', 'Unknown URL type'))}'></i> "
            f"<span class='input-monospace' style='font-size: 0.8rem;'>{_esc(asset_id)}</span></a> "
            f"{delete_button}"
        )

    return f"<span class='text-nowrap'>{_esc(label)} {delete_button}</span>"
