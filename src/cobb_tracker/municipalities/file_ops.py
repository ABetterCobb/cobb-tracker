from pathlib import Path
import sys
import os
import requests
from cobb_tracker.cobb_config import cobb_config
from threading import BoundedSemaphore
from threading import Thread

class file_ops():
    def __init__(self,
                session: requests.Session,
                user_agent: str,
                file_urls: dict,
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
        self.maxconnections = 15
        self.pool_sema = BoundedSemaphore(value=self.maxconnections)

        self.session = session
        self.user_agent = user_agent
        self.file_urls = file_urls
        self.config = config

    def write_minutes_doc(self):
        url_threads = [Thread(target=self.pull_minutes_doc, args=(url,)) for url in self.file_urls]

        for thread in url_threads:
            thread.start()
        for thread in url_threads:
            thread.join()


    def pull_minutes_doc(self, url: str):
        with self.pool_sema:
            url = ''.join(map(str, url))
            municipality = self.file_urls[url]["municipality"]
            meeting_type = self.file_urls[url]["meeting_name"]
            file_url = url
            doc_date = self.file_urls[url]["date"]
            file_type = self.file_urls[url]["file_type"]
            pdf_path = Path(
                        Path(self.config.get_config("directories", "minutes_dir"))
                        .joinpath(municipality,meeting_type)
                        )
            #normalize
            meeting_type = meeting_type.lower()

            doc_name=f"{doc_date}-{file_type}.pdf"
            doc_full_path=os.path.join(pdf_path,doc_name)

            if not os.path.exists(doc_full_path):
                pdf_path.mkdir(parents=True, exist_ok=True)
                response = requests.get(file_url, headers={"User-Agent": self.user_agent})
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
class file_get():        
    def __init__(self, minutes_dir: str) -> list:
        all_files = []
        def list_all_files(minutes_dir: str):
            for entry in os.scandir(minutes_dir):
                if entry.is_file():
                    all_files.append(entry.path)
                if entry.is_dir():
                    list_all_files(entry)
        list_all_files(minutes_dir)
        return all_files
