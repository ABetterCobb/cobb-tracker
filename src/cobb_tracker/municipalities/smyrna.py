from cobb_tracker.municipalities import file_ops
from cobb_tracker.cobb_config import CobbConfig
import requests
import json
import re

from datetime import datetime

import pathlib
import sys
import os

"""Smyrna's website (https://smyrnaga.primegov.com) is powered by PrimeGov. 
   As of 2023-12-26 we have access the API
"""
BASE_URL = "https://smyrnaga.primegov.com/api/v2/PublicPortal"
MEETINGS_URL = f"{BASE_URL}/ListArchivedMeetings?year="
MINUTES_URL = f"https://smyrnaga.primegov.com/Public/CompiledDocument?meetingTemplateId="
#[num]&compileOutputType=1

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)
def get_all_events(session: requests.Session) -> dict:
    """BASE_URL combined with MEETINGS_URL will give you a list of all meetings for a given year
    Each of these meetings will at least have an HTML Agenda, and depending on when the meeting
    took place it will also have either an Agenda or Minutes file
    """
    event_list = []
    for year in range(2013,int(datetime.now().year)+1):
        raw_event_page = json.loads(session.get(f"{MEETINGS_URL}{year}",
                                                headers={"User-Agent": USER_AGENT}).text)
        event_list[year] = raw_event_page 
    return event_list

def get_minutes_docs(config: CobbConfig):
    minutes_urls = {}
    session = requests.Session()
    for event in get_all_events(session):
        print(event)
#        event_date = datetime.fromisoformat(
#                event["eventDate"]
#                ).strftime("%Y-%m-%d")
#        for file in event["publishedFiles"]:
#            file_url = f"{MEETINGS_URL}GetMeetingFileStream(fileId={file['fileId']},plainText=false)"
#            if file["type"] == "Minutes":
#                minutes_urls[file_url] = {}
#                minutes_urls[file_url]["municipality"] = "Cobb"
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
