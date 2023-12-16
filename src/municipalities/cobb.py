import requests
import json
from datetime import datetime
import municipalities.file_ops

import pathlib
import sys
import os

BASE_URL = "https://cobbcoga.api.civicclerk.com/v1"
EVENTS_URL = f"{BASE_URL}/Events/"
MEETINGS_URL = f"{BASE_URL}/Meetings/"

def get_minutes_docs():
    event_list = json.loads(requests.get(EVENTS_URL).text)["value"]

    for event in event_list:
        event_type = event["categoryName"].replace(' ','_')
        event_date = datetime.fromisoformat(
                event["eventDate"]
                ).strftime("%Y-%m-%d")
        print(event_type)

        for file in event["publishedFiles"]:
            file_url = f"{MEETINGS_URL}GetMeetingFileStream(fileId={file['fileId']},plainText=false)"
            file_contents = requests.get(file_url).content
            print(file_url)
            pdf_path = pathlib.Path(os.getcwd()).joinpath("minutes","Cobb",event_type,event_date,file["type"])

            municipalities.file_ops.write_minutes_doc(
                    doc_date=event_date,
                    pdf_file=file_contents,
                    pdf_path=pdf_path,
                    municipality="Cobb"
                )

            #pdf_path.mkdir(parents=True, exist_ok=True)

            #with open(pdf_path.joinpath(f"{event_date}.pdf"), "wb") as file:
            #    file.write(file_contents)
            #print(json.dumps(file, indent=4))
