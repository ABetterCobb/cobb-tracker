from datetime import datetime
import concurrent.futures as cf
import logging

import json
import requests

from cobb_tracker.cobb_config import CobbConfig
from cobb_tracker import file_ops

BASE_URL = "https://acworthcityga.iqm2.com/"
# Agenda is type 15, then you specify the ID
BASE_FILE_URL = f"{BASE_URL}Citizens/FileOpen.aspx?"
STARTUP_URL = f"{BASE_URL}/api/Agency/StartupData"
MEETINGS_URL = f"{BASE_URL}api/Meeting?"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"


def get_all_events(session: requests.Session) -> list:
    """BASE_URL is the base url where events
    are being pulled from. The page will only give you 15 events at a time, and
    the link to get the next 15 is contained in @odata.nextLink

    """

    def get_event(group: dict, years: int, session: requests.Session):
        group_id = group["ID"]
        for year in years:
            event_page = json.loads(
                session.get(
                    f"{MEETINGS_URL}Range={year}&Group={group_id}/",
                    headers={"User-Agent": USER_AGENT},
                ).text
            )
            event_list.append(event_page)

    startup_page = json.loads(
        session.get(STARTUP_URL, headers={"User-Agent": USER_AGENT}).text
    )
    meeting_ranges = startup_page["MeetingRanges"]
    meeting_groups = startup_page["MeetingGroups"]
    years = []
    event_list = []

    for entry in meeting_ranges:
        if entry["ID"] != 1:
            years.append(entry["ID"])

    with cf.ThreadPoolExecutor(max_workers=15) as executor:
        future_groups = {
            executor.submit(get_event, group, years, session): group
            for group in meeting_groups
        }
        for _ in cf.as_completed(future_groups):
            pass

    return event_list


def get_minutes_docs(config: CobbConfig):
    """
    This will format the data and pass it off FileOps to be downloaded
    and written to the filesystem
    """
    minutes_urls = {}
    session = requests.Session()
    for event_list in get_all_events(session):
        for event in event_list:
            if "Minutes" in event:
                meeting_info = event["Meeting"]
                body = meeting_info["Department"]["Name"]
                meeting_type = meeting_info["Type"]["Name"]
                try:
                    event_type = body.lstrip().replace(" ", "_")
                except Exception as e:
                    logging.error(
                        f"Error: couldn't retrieve for Event. \nID: {meeting_info['ID']} \nName: {body} {meeting_type} {e}"
                    )
                    event_type = "misc"

                event_date = datetime.fromisoformat(
                    meeting_info["Date"]
                ).strftime("%Y-%m-%d")

                file_url = f"{event['Minutes']['Documents'][0]['DownloadURL']}"
                minutes_urls[file_url] = {}
                minutes_urls[file_url]["municipality"] = "Acworth"
                minutes_urls[file_url]["meeting_name"] = event_type
                minutes_urls[file_url]["date"] = event_date
                minutes_urls[file_url]["file_type"] = "minutes"

        doc_ops = file_ops.FileOps(
            file_urls=minutes_urls,
            session=session,
            user_agent=USER_AGENT,
            config=config,
        )
        doc_ops.write_minutes_doc()
