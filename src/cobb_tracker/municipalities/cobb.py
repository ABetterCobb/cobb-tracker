from cobb_tracker.municipalities import file_ops
from cobb_config import cobb_config
import requests
import json
import re

from datetime import datetime

import pathlib
import sys
import os

BASE_URL = "https://cobbcoga.api.civicclerk.com/v1"
EVENTS_URL = f"{BASE_URL}/Events/"
MEETINGS_URL = f"{BASE_URL}/Meetings/"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)
def get_all_events(session: requests.Session) -> dict:

    raw_event_page = json.loads(session.get(EVENTS_URL,
                                            headers={"User-Agent": USER_AGENT}).text)
    event_list = raw_event_page["value"]
    next_event_set_link = raw_event_page["@odata.nextLink"]

    while True:
        next_event_list = json.loads(session.get(next_event_set_link,
                                                 headers={"User-Agent": USER_AGENT}).text)
        event_list = event_list + next_event_list["value"] 
        if "@odata.nextLink" in next_event_list.keys():
            next_event_set_link = next_event_list["@odata.nextLink"]
        else:
            break
    return event_list

def get_minutes_docs(config: cobb_config):
    session = requests.Session()
    for event in get_all_events(session):
        try:
            event_type = event["categoryName"].lstrip().replace(' ','_')
        except:
            print("Error retrieving categoryName")
            event_type = "misc"

        event_date = datetime.fromisoformat(
                event["eventDate"]
                ).strftime("%Y-%m-%d")
        for file in event["publishedFiles"]:
            file_url = f"{MEETINGS_URL}GetMeetingFileStream(fileId={file['fileId']},plainText=false)"
            pdf_path = pathlib.Path(os.getcwd()).joinpath("minutes","Cobb",event_type)
            
            if file["type"] == "Minutes":
                file_ops.write_minutes_doc(
                    doc_date=event_date,
                    meeting_type=file["type"],
                    event_type=event_type,
                    file_url=file_url,
                    session=session,
                    user_agent=USER_AGENT,
                    municipality="Cobb",
                    config=config
                )
