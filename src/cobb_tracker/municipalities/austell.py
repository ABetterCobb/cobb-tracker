"""
Austell

Austell is split into two websites. The first is the Past Agendas and Minutes page on the website,
the second is under municode meetings. All new agendas and minutes packets are hosted on the municode
meetings website. Municode meetings is now owned by CivicPlus, but maintains it's own publicly 
accessible API.

"""
import logging
import requests
import json

from cobb_tracker.string_ops import parse_date
from cobb_tracker import file_ops
from cobb_tracker.cobb_config import CobbConfig

from bs4 import BeautifulSoup

URL_BASE = "https://www.austellga.gov/"
NEW_AGENDA_PAGE = "https://austell-ga.municodemeetings.com/"
AGENDA_PAGES = CURRENT_MINUTES = [
    f"{URL_BASE}PastAgendasandMinutes.aspx"
]
# FILE_PAGE = f"{LIST_OF_ARCHIVE_SECTIONS}?ADID="
minutes_urls = {}
muni = "Austell"
session = requests.Session()


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"


def get_minutes_docs(config: CobbConfig) -> int:
    urls = {}
    for page in AGENDA_PAGES:
        response = session.get(page, headers={"User-Agent": USER_AGENT})

        if not response.ok:
            logging.error(
                f"Request failed: {response.reason} {response.status_code}"
            )
            return 0
        current_minutes_page = BeautifulSoup(response.text, "html.parser")
        years_container = current_minutes_page.find(
            "div", class_="mcms_RendererContentDetail"
        )
        minutes_divs = [
            div
            for div in years_container.find_all("div")
            if div.find("h3") is not None and div.find("h3").text == "Minutes"
        ]

        for div in minutes_divs:
            new_urls = {
                f"{URL_BASE}{url.get('href')}": parse_date(url.text)
                for url in div.find_all("a")
            }
            urls = urls | new_urls
    for url in urls.keys():
        minutes_urls[url] = {}
        minutes_urls[url]["municipality"] = "Austell"
        minutes_urls[url]["meeting_name"] = "City_Council"
        minutes_urls[url]["date"] = urls[url]
        minutes_urls[url]["muni_body"] = "City Council"
        minutes_urls[url]["file_type"] = "minutes"

    # Pulls a list of all meetings
    response = session.get(NEW_AGENDA_PAGE + "api/v1/public/meeting/list.json", headers={"User-Agent": USER_AGENT})
    if not response.ok:
        logging.error(
            f"Request failed: {response.reason} {response.status_code}"
        )
        return 0

    meetings_list = response.json()
    for meeting in meetings_list["Meetings"]:
        meeting_id = meeting["MeetingID"]
        meeting_details = session.get(NEW_AGENDA_PAGE + f"/api/v1/public/meeting/{meeting_id}/details.json", headers={"User-Agent": USER_AGENT}).json()["Meetings"][0]

        if "MinutesLinks" in meeting_details: 
            url = meeting_details["MinutesLinks"][0]["MinutesLinksURL"]
            minutes_urls[url] = {}
            minutes_urls[url]["municipality"] = "Austell"
            minutes_urls[url]["meeting_name"] = meeting["GroupName"]
            minutes_urls[url]["muni_body"] = meeting["GroupName"]
            minutes_urls[url]["date"] = meeting["CalendarDate"][0]["FromDate"]
            minutes_urls[url]["file_type"] = "minutes"
        
    doc_ops = file_ops.FileOps(
        file_urls=minutes_urls,
        session=session,
        user_agent=USER_AGENT,
        config=config,
    )



    doc_ops.write_minutes_doc()
    return len(minutes_urls)
    
