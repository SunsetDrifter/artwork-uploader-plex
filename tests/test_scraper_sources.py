"""
Homelab fork: only ThePosterDB and MediUX URLs are scraped.

Any URL containing ".html" used to be routed to the ThePosterDB scraper whatever its host, so
pasting http://<a mesh host>/set/x.html made the container fetch internal addresses and echo
parts of the reply back as the set title and author.
"""

import pytest

import scrapers.scraper as scraper_module
from core.enums import ScraperSource
from core.exceptions import ScraperException
from scrapers.scraper import Scraper


@pytest.mark.unit
@pytest.mark.parametrize("url", [
    "http://100.109.122.35:32400/set/x.html",
    "https://intranet.example/poster/1.html",
    "file:///etc/passwd.html",
])
def test_an_html_url_on_another_host_is_refused_without_fetching(monkeypatch, url):
    fetched = []
    monkeypatch.setattr(scraper_module, "ThePosterDBScraper", lambda *a, **k: fetched.append(a) or None)

    with pytest.raises(ScraperException):
        Scraper(url, None).scrape()

    assert fetched == []


@pytest.mark.unit
@pytest.mark.parametrize("url,source", [
    ("https://theposterdb.com/set/12345", ScraperSource.THEPOSTERDB.value),
    ("https://mediux.pro/sets/12345", ScraperSource.MEDIUX.value),
])
def test_the_real_sources_are_still_recognised(url, source):
    assert Scraper(url, None).source == source
