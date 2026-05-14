"""Acworth's live source — Granicus.

Replaces the IQM2 archive at acworth.py for current ingest.
Pulls Agenda + Minutes per meeting from the single Granicus ViewPublisher page.
"""
import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from cobb_tracker import file_ops
from cobb_tracker.cobb_config import CobbConfig

BASE = "https://acworth-ga.granicus.com"
LISTING_URL = f"{BASE}/ViewPublisher.php?view_id=1"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"

WHITESPACE_RE = re.compile(r"\s+")


def _parse_date(raw: str) -> str | None:
    """The date cell looks like 'Jan\xa028,\xa02026  -  05:00\xa0PM' — drop the
    time after the dash, normalize whitespace, parse to YYYY-MM-DD."""
    text = raw.replace("\xa0", " ").split("-")[0]
    text = WHITESPACE_RE.sub(" ", text).strip()
    try:
        return datetime.strptime(text, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _absolute(href: str) -> str:
    if href.startswith("//"):
        return f"https:{href}"
    return href


def get_minutes_docs(config: CobbConfig) -> int:
    session = requests.Session()
    response = session.get(LISTING_URL, headers={"User-Agent": USER_AGENT})
    if not response.ok:
        logging.error(
            f"Acworth Granicus request failed: {response.reason} {response.status_code}"
        )
        return 0

    soup = BeautifulSoup(response.content, "html.parser")
    file_urls = {}

    for panel in soup.find_all("div", class_="CollapsiblePanel"):
        tab = panel.find("div", class_="CollapsiblePanelTab")
        if tab is None:
            continue
        body_name = tab.text.strip()
        muni_body = body_name.replace(" ", "_")

        for row in panel.find_all("tr", class_="listingRow"):
            cells = row.find_all("td", class_="listItem")
            if len(cells) < 4:
                continue

            date_str = _parse_date(cells[1].text)
            if date_str is None:
                logging.error(
                    f"Acworth Granicus: couldn't parse date for {body_name}: "
                    f"'{cells[1].text.strip()}'"
                )
                continue

            for cell, file_type in ((cells[2], "agenda"), (cells[3], "minutes")):
                link = cell.find("a")
                if link is None:
                    continue
                href = link.get("href")
                if not href:
                    continue
                url = _absolute(href)
                file_urls[url] = {
                    "municipality": "Acworth",
                    "muni_body": muni_body,
                    "meeting_name": muni_body,
                    "date": date_str,
                    "file_type": file_type,
                }

    if file_urls:
        doc_ops = file_ops.FileOps(
            file_urls=file_urls,
            session=session,
            user_agent=USER_AGENT,
            config=config,
        )
        doc_ops.write_minutes_doc()
    return len(file_urls)
