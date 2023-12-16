import municipalities.file_ops

import requests
import json
import re

from datetime import datetime

import pathlib
import sys
import os
import asyncio

BASE_URL = "https://cobbcoga.api.civicclerk.com/v1"
EVENTS_URL = f"{BASE_URL}/Events/"
MEETINGS_URL = f"{BASE_URL}/Meetings/"

def get_all_events() -> dict:

    raw_event_page = json.loads(requests.get(EVENTS_URL).text)
    event_list = raw_event_page["value"]
    next_event_set_link = raw_event_page["@odata.nextLink"]

    while True:
        next_event_list = json.loads(requests.get(next_event_set_link).text)
        event_list = event_list + next_event_list["value"] 
        if "@odata.nextLink" in next_event_list.keys():
            next_event_set_link = next_event_list["@odata.nextLink"]
        else:
            break
    return event_list

def get_minutes_docs():
    
    for event in get_all_events():
        try:
            event_type = event["categoryName"].lstrip().replace(' ','_')
        except:
            print("Error retrieving categoryName")
            event_type = "misc"

        event_date = datetime.fromisoformat(
                event["eventDate"]
                ).strftime("%Y-%m-%d")
        print(event_type)
            
        for file in event["publishedFiles"]:
            file_url = f"{MEETINGS_URL}GetMeetingFileStream(fileId={file['fileId']},plainText=false)"
            pdf_path = pathlib.Path(os.getcwd()).joinpath("minutes","Cobb",event_type)
            
            if file["type"] == "Minutes":
                asyncio.run(
                        municipalities.file_ops.write_minutes_doc(
                        doc_date=event_date,
                        meeting_type=file["type"],
                        file_url=file_url,
                        pdf_path=pdf_path,
                        municipality="Cobb"
                    )
                )
