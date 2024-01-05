from cobb_tracker.municipalities import file_ops
from cobb_tracker.cobb_config import CobbConfig
import requests
import json
import re

from datetime import datetime


"""Smyrna's website (https://smyrnaga.primegov.com) is powered by PrimeGov. 
   As of 2023-12-26 we have access the API
"""
BASE_URL = "https://smyrnaga.primegov.com/api/v2/PublicPortal"
MEETINGS_URL = f"{BASE_URL}/ListArchivedMeetings?year="
MINUTES_URL = "https://smyrnaga.primegov.com/Public/CompiledDocument?meetingTemplateId="
#[num]&compileOutputType=1

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)
def get_all_events(session: requests.Session) -> dict:
    """BASE_URL combined with MEETINGS_URL will give you a list of all meetings for a given year
    Each of these meetings will at least have an HTML Agenda, and depending on when the meeting
    took place it will also have either an Agenda or Minutes file
    """
    event_list = {}

    #The records on Smyrna's primegov site only go back to 2013
    for year in range(2013,int(datetime.now().year)+1):
        raw_event_page = json.loads(session.get(f"{MEETINGS_URL}{year}",
                                                headers={"User-Agent": USER_AGENT}).text)
        event_list[year] = raw_event_page 
    return event_list

def get_minutes_docs(config: CobbConfig):
    minutes_urls = {}

    #The clerk was having too much fun with the meeting titles
    smyrna_clean = [r' on \d{4}-\d{2}-\d{2}(.*)$',
                    r':(.*)',
                    r'\s?\d{2}-\d{2}-\d{4}\s?',
                    r'(\b\d{1,2}\D{0,3})?\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)\D?(\d{1,2}\D?)?\D?((19[7-9]\d|20\d{2})|\d{2})\s?',
                    r'(^\s?)?(\s?$)?',
                    r'(\s-(.*))?( Meeting)?(\sNotice\sand\sAgenda)?']

    session = requests.Session()
    event_data = get_all_events(session)

    for year in event_data:
        for event in event_data[year]:
            event_date = datetime.strptime(
                    event["date"],
                    "%b %d, %Y"
                    ).strftime("%Y-%m-%d")

            for file in event["documentList"]:
                if file["templateName"] == "Minutes":

                    #The title might have new lines in it
                    event_title = event["title"].replace('\n','')
                    
                    for regex in smyrna_clean: 
                        event_title = re.sub(regex,'',event_title)
                    
                    file_url = f"{MINUTES_URL}{file['templateId']}"
                    minutes_urls[file_url] = {}
                    minutes_urls[file_url]["municipality"] = "Smyrna"
                    minutes_urls[file_url]["meeting_name"] = event_title.replace(' ','_')
                    minutes_urls[file_url]["date"] = event_date 
                    minutes_urls[file_url]["file_type"] = "minutes" 

    doc_ops = file_ops.FileOps(
        file_urls=minutes_urls,
        session=session,
        user_agent=USER_AGENT,
        config=config
       )
    doc_ops.write_minutes_doc()
