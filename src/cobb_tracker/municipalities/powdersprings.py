import requests
import re
import os
import sys
from cobb_tracker.municipalities import file_ops
from cobb_tracker.cobb_config import CobbConfig

from bs4.element import Tag
from bs4 import BeautifulSoup

URL_BASE = "https://cityofpowdersprings.org/"
LIST_OF_ARCHIVE_SECTIONS = f"{URL_BASE}Archive.aspx"
BASE_FILE_URL = f"{URL_BASE}ArchiveCenter/ViewFile/Item/"
get_year = re.compile(r'((\b(?:(Jan|JAN)(?:uary)?|(FEB|Feb)(?:ruary)?|(Mar|MAR)(?:ch)?|(Apr|APRIL)(?:il)?|(May|MAY)|(Jun|JUNE)(?:e)?|(JULY|Jul)(?:y)?|(AUG|Aug)(?:ust)?|(Sep|Sept|SEPT)(?:tember)?|(OCT|Oct)(?:ober)?|(Nov|NOV|Dec|DEC)(?:ember)?)\s?(\.|,)?\s?(\d{1,2}\D?)?\D?\s?((19[7-9]\d|20\d{2})))|(\d{1,2}(\.|/|-|,)\s?\d{1,2}(\.|/|-|,)\s?\d{2,4})|([0-1][1-9][0-2][0-9][0-9][0-9]))')

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )
def get_minutes_docs(config: CobbConfig):
    session = requests.Session()
    archive_groups = {} 
    response = session.get(LIST_OF_ARCHIVE_SECTIONS, headers={"User-Agent": USER_AGENT})
    if not response.ok:
        print("Request failed:", response.reason, response.status_code)
        return
    soup = BeautifulSoup(response.text, 'html.parser')
    archive_details = soup.find("table", summary="Archive Details")

    for select_tag in archive_details.find_all("select"):
        for label in archive_details.find_all("label"):
            if label.get("for") == select_tag.get("id"):
                group = label.text.replace(":","")
                group_id = re.sub(r'[a-zA-Z]',
                                          '',
                                          select_tag.get("id"))
                archive_groups[group_id] = group

    for group in archive_groups.keys():
        if archive_groups[group] != "Press Releases" and archive_groups[group] != "Town Hall Meetings and Retreats":
            group_page = f"{LIST_OF_ARCHIVE_SECTIONS}?AMID={group}&Type=&ADID="
            archive_page_response = session.get(group_page, headers={"User-Agent": USER_AGENT})
            if not archive_page_response.ok:
                print("Request failed:", archive_page_response.reason, archive_page_response.status_code)
                return
            archive_page = BeautifulSoup(archive_page_response.text, 'html.parser')
            all_meetings = archive_page.find_all("span", class_="archive")
            for span in all_meetings:
                lines = [ line for line in span.text.split('\n') if line.strip()]
                link = span.find("a")
                name = span.find("span")
                if link is not None and name is not None: 
                    result = get_year.search(str(name.text))
                    if result is not None:
                        print(result.group(0))
                    else:
                        print(name.text)
                    file_id = re.sub(r'[a-zA-Zw\.\?=]','',link.get('href'))
                    print(f"{BASE_FILE_URL}{file_id}")


