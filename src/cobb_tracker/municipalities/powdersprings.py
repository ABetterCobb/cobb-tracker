import requests
import re
import os

from cobb_tracker.municipalities import file_ops
from cobb_tracker.cobb_config import CobbConfig

from bs4.element import Tag
from bs4 import BeautifulSoup

URL_BASE = "https://cityofpowdersprings.org/"
LIST_OF_ARCHIVE_SECTIONS = f"{URL_BASE}Archive.aspx"
BASE_FILE_URL = f"{URL_BASE}ArchiveCenter/ViewFile/Item/"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )
def get_minutes_docs(config: CobbConfig):
    session = requests.Session()
    archive_ids = []
    response = session.get(LIST_OF_ARCHIVE_SECTIONS, headers={"User-Agent": USER_AGENT})
    if not response.ok:
        print("Request failed:", response.reason, response.status_code)
        return
    soup = BeautifulSoup(response.text, 'html.parser')
    archive_details = soup.find("table", summary="Archive Details")

    for select_tag in archive_details.find_all("select"):
        archive_group_ids.append(re.sub(r'[a-zA-Z]',
                                  '',
                                  select_tag.get("id")))

    for group in archive_group_ids:
        group_page = f"{LIST_OF_ARCHIVE_SECTIONS}?AMID={group}&Type=&ADID="
        archive_page_response = session.get(LIST_OF_ARCHIVE_SECTIONS, headers={"User-Agent": USER_AGENT})

        if not response.ok:
            print("Request failed:", response.reason, response.status_code)
            return
        
        archive_page = soup.BeautifulSoup(archive_page_response.text, 'html.parser')
        print(archive_page)
        
