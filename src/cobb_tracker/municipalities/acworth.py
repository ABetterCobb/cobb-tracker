from cobb_tracker.municipalities import file_ops
from cobb_tracker.cobb_config import CobbConfig
import requests
import json
import re

from datetime import datetime

import pathlib
import sys
import os

BASE_URL = "acworthcityga.iqm2.com/"
#Agenda is type 15, then you specify the ID
BASE_FILE_URL = f"{BASE_URL}Citizens/FileOpen.aspx?"
STARTUP_URL = f"{BASE_URL}/api/Agency/StartupData"
MEETINGS_URL = f"{BASE_URL}api/Meetings?"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)
def get_all_events(session: requests.Session) -> dict:

    """BASE_URL is the base url where events
       are being pulled from. The page will only give you 15 events at a time, and 
       the link to get the next 15 is contained in @odata.nextLink

    """
    raw_startup_page = json.loads(session.get(STARTUP_URL,
                                            headers={"User-Agent": USER_AGENT}).text)
    event_list = raw_event_page["value"]

def get_minutes_docs( config: CobbConfig):
    minutes_urls = {}
    session = requests.Session()
    print(get_all_events(session))
#    for event in get_all_events(session):
#        try:
#            event_type = event["categoryName"].lstrip().replace(' ','_')
#        except:
#            print(f"Error: couldn't retrieve categoryName for Event. \nID: {event['id']} \nName: {event['eventName']} ")
#            event_type = "misc"
#
#        event_date = datetime.fromisoformat(
#                event["eventDate"]
#                ).strftime("%Y-%m-%d")
#        for file in event["publishedFiles"]:
#            file_url = f"{MEETINGS_URL}GetMeetingFileStream(fileId={file['fileId']},plainText=false)"
#            if file["type"] == "Minutes":
#                minutes_urls[file_url] = {}
#                minutes_urls[file_url]["municipality"] = "acworth"
#                minutes_urls[file_url]["meeting_name"] = event_type 
#                minutes_urls[file_url]["date"] = event_date 
#                minutes_urls[file_url]["file_type"] = "minutes" 
#
#
#    doc_ops = file_ops.FileOps(
#        file_urls=minutes_urls,
#        session=session,
#        user_agent=USER_AGENT,
#        config=config
#       )
#    doc_ops.write_minutes_doc()
