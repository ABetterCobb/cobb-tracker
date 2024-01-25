from cobb_tracker import file_ops
import logging
from cobb_tracker.cobb_config import CobbConfig
import requests
import json

from datetime import datetime


class CivicPlus: 
    def __init__(self, base_url: str, muni: str):
        self.BASE_URL = base_url 
        self.EVENTS_URL = f"{self.BASE_URL}/Events/"
        self.MEETINGS_URL = f"{self.BASE_URL}/Meetings/"
        self.MUNI = muni

        self.USER_AGENT = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        )
    def get_all_events(self,session: requests.Session) -> dict:

        """BASE_URL is the base url where events
           are being pulled from. The page will only give you 15 events at a time, and 
           the link to get the next 15 is contained in @odata.nextLink

        """
        raw_event_page = json.loads(session.get(self.EVENTS_URL,
                                                headers={"User-Agent": self.USER_AGENT}).text)
        event_list = raw_event_page["value"]
        next_event_set_link = raw_event_page["@odata.nextLink"]

        while True:
            next_event_list = json.loads(session.get(next_event_set_link,
                                                     headers={"User-Agent": self.USER_AGENT}).text)
            event_list = event_list + next_event_list["value"] 
            if "@odata.nextLink" in next_event_list.keys():
                next_event_set_link = next_event_list["@odata.nextLink"]
            else:
                break
        return event_list

    def get_minutes_docs(self, config: CobbConfig):
        minutes_urls = {}
        session = requests.Session()
        for event in self.get_all_events(session):
            try:
                event_type = event["categoryName"].lstrip().replace(' ','_')
            except Exception as e:
                logging.error(f"couldn't retrieve categoryName for Event. \nID: {event['id']} \nName: {event['eventName']} {e} ")
                event_type = "misc"

            event_date = datetime.fromisoformat(
                    event["eventDate"]
                    ).strftime("%Y-%m-%d")
            for file in event["publishedFiles"]:
                file_url = f"{self.MEETINGS_URL}GetMeetingFileStream(fileId={file['fileId']},plainText=false)"
                if file["type"] == "Minutes":
                    minutes_urls[file_url] = {}
                    minutes_urls[file_url]["municipality"] = self.MUNI
                    minutes_urls[file_url]["meeting_name"] = event_type 
                    minutes_urls[file_url]["date"] = event_date 
                    minutes_urls[file_url]["file_type"] = "minutes" 


        doc_ops = file_ops.FileOps(
            file_urls=minutes_urls,
            session=session,
            user_agent=self.USER_AGENT,
            config=config
           )
        doc_ops.write_minutes_doc()
