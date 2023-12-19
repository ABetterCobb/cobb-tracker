from pathlib import Path
import sys
import os
import requests
from cobb_tracker.cobb_config import cobb_config

def write_minutes_doc(
            doc_date: str, 
            session: requests.Session,
            meeting_type: str,
            user_agent: str,
            file_url: str,
            municipality: str,
            file_type: str,
            config: cobb_config
        ):
    """Download and write minutes file for the specified meeting to disk
    
    Args:
        doc_date (str): The date the event took place in the format YYYY-MM-D   
        session (requests.Session): requests session object

        meeting_type (str): What type of meeting was this?
        user_agent (str): User agent for requests session object
        file_url (str): Where is this file located?

        municipality (str): This will either be Cobb County or one of it's cities.
        file_type (str): Is this an agenda or minute file?
        config (cobb_config): cobb_config object to get user specific config
    """
    pdf_path = Path(
                Path(config.get_config("directories", "minutes_dir"))
                .joinpath(municipality,meeting_type)
                )
    if not os.path.exists(pdf_path):

        pdf_path.mkdir(parents=True, exist_ok=True)
        meeting_type = meeting_type.lower()
        doc_name=f"{doc_date}-{file_type}.pdf"

        reponse = requests.get(file_url, headers={"User-Agent": user_agent})
        if not response.ok:
            print(
                "Error retrieving minutes document:",
                    meeting_type,
                    doc_name,
                    response.reason,
            )
        return
        pdf_file = response.content

        with open(pdf_path.joinpath(doc_name), "wb") as file:
            file.write(pdf_file)
            print(f"{doc_name} -> {pdf_path}/{doc_name}")
    else:
        print("File exists")
def minutes_files(minutes_dir: str) -> list:
    all_files = []
    def list_all_files(minutes_dir: str):
        for entry in os.scandir(minutes_dir):
            if entry.is_file():
                all_files.append(entry.path)
            if entry.is_dir():
                list_all_files(entry)
    list_all_files(minutes_dir)
    return all_files
