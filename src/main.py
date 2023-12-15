import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

URL_BASE = "https://www.mariettaga.gov"
URL_AGENDAS = f"{URL_BASE}/AgendaCenter"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)

MINUTES_FOLDER = pathlib.Path(__file__).parent.joinpath("minutes")

RE_ALPHNUM = re.compile(r"[^a-zA-Z0-9]")
RE_ALPHA = re.compile(r"[0-9\.\-]")


def clean_name(input_string: str):
    """Use regex to replace non-alphanumeric characters with underscores"""
    # TODO: This is a little messy and leaves some errant "_" at the end of some folders.
    input_string = RE_ALPHA.sub("", input_string)
    result_string = (
        RE_ALPHNUM.sub("_", input_string).replace("__", "_").replace("__", "_")
    )
    return result_string

def is_year(input_string: str):
    year = re.compile(r'\d{4}')
    if year.match(input_string):
        return True
    else:
        return False
def get_years(agenda_container: str):
    year_list = agenda_container.find("ul", class_="years")
    filtered_year_list = []
    for entry in year_list.find_all("li"):
        entry_string = entry.find("a").text
        if is_year(entry_string):
            filtered_year_list.append(entry_string)
    return filtered_year_list
def get_minutes_docs():
    MINUTES_FOLDER.mkdir(exist_ok=True)
    session = requests.Session()

    response = session.get(URL_AGENDAS, headers={"User-Agent": USER_AGENT})
    if not response.ok:
        print("Request failed:", response.reason, response.status_code)
        return

    soup = BeautifulSoup(response.content, "html.parser")
    agenda_containers = soup.find_all("div", class_="listing listingCollapse noHeader")
    for container in agenda_containers:
        year_list = get_years(container)
        year_list[::]
        sys.exit()
        rows = container.find_all("tr", class_="catAgendaRow")
        for row in rows:
            meeting_title = row.find("a", {"aria-describedby": True}, target="_blank")
            if meeting_title is None:
                continue
            meeting_name = clean_name(meeting_title.text.strip().title())

            date_header = row.find("td", class_=None)
            print(date_header.strong.get_text() + " " + date_header.p.get_text().strip())

            minutes = row.find("td", class_="minutes")
            minutes_link = minutes.find("a")

            if not minutes_link:
                continue

            minutes_url = f"{URL_BASE}{minutes_link.get('href')}"
            minutes_name = minutes_url.split("/")[-1]

            doc_id = minutes_name.split("-")[1]
            year = minutes_name[5:9]
            month = minutes_name[1:3]
            day = minutes_name[3:5]

            new_name = f"{year}_{month}_{day}_minutes_{doc_id}.pdf"

            meeting_folder = MINUTES_FOLDER.joinpath(meeting_name)
            meeting_folder.mkdir(exist_ok=True)

            minutes_doc = session.get(minutes_url, headers={"User-Agent": USER_AGENT})
            if minutes_doc.ok:
                file_path = meeting_folder.joinpath(new_name)
                if file_path.exists():
                    continue

                with open(file_path, "wb") as outfile:
                    outfile.write(minutes_doc.content)


if __name__ == "__main__":
    get_minutes_docs()
