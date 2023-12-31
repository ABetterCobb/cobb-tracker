from pathlib import Path
import sys
import os
import requests
import concurrent.futures as cf
from cobb_tracker.cobb_config import CobbConfig
import hashlib

class FileOps():
    def __init__(self,
                session: requests.Session,
                user_agent: str,
                file_urls: dict,
                config: CobbConfig
                ):
        """
        Args:
            session (requests.Session): requests session object
            user_agent (str): User agent for requests session object
            file_url (str): Where is this file located?
            config (CobbConfig): CobbConfig object to get user specific config
        """
        self.maxconnections = 15
        self.session = session
        self.user_agent = user_agent
        self.file_urls = file_urls
        self.config = config

    def write_minutes_doc(self):
        with cf.ThreadPoolExecutor(max_workers=self.maxconnections) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.pull_minutes_doc, url): url for url in self.file_urls}
            for _ in cf.as_completed(future_to_url):
                pass

    def pull_minutes_doc(self, url: str):
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

        args = self.config.args
        if not os.path.exists(doc_full_path) or args.force:
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
            return

class FileList():        
    def __init__(self, minutes_dir: str) -> list:
        self.minutes_dir = minutes_dir 

    
    def get_checksum(self, minutes_file: Path):
        BUFFER=(1024 ** 2) * 3
        m = hashlib.sha256()
        with open(minutes_file,'rb') as file:
            while True:
                chunk = file.read(BUFFER)
                if not chunk:
                    break
                m.update(chunk)
        return m.hexdigest()
    def minutes_files(self):
        all_files = []
        def list_all_files(path: str):
            for entry in os.scandir(path):
                if entry.is_file():
                    all_files.append(entry.path)
                if entry.is_dir():
                    list_all_files(entry)
        list_all_files(self.minutes_dir)
        return all_files
