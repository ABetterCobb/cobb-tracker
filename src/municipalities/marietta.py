import requests
import pathlib
import re

from bs4.element import Tag
from bs4 import BeautifulSoup

URL_BASE = "https://www.mariettaga.gov"
URL_AGENDAS = f"{URL_BASE}/AgendaCenter"
URL_UPDATE_AGENDAS = f"{URL_BASE}/AgendaCenter/UpdateCategoryList"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)

MINUTES_FOLDER = pathlib.Path(__file__).parent.joinpath("minutes")

RE_ALPHNUM = re.compile(r"[^a-zA-Z0-9]")
RE_ALPHA = re.compile(r"[0-9\.\-]")

def process_row_documents(row: Tag, session: requests.Session, container_name: str) -> None:
    """Parse meeting information and documents from a table row.

    Args:
        row (Tag): Row from a Marietta meeting list table.
        session (requests.Session): Session object for doing HTTP calls.
    """
    meeting_title = row.find("a", {"aria-describedby": True}, target="_blank")
    if meeting_title is None:
        return
    meeting_name = clean_name(meeting_title.text.strip().title())

    date_header = row.find("td", class_=None)

    minutes = row.find("td", class_="minutes")
    minutes_link = minutes.find("a")

    if not minutes_link:
        return

    minutes_url = f"{URL_BASE}{minutes_link.get('href')}"
    minutes_name = minutes_url.split("/")[-1]

    doc_id = minutes_name.split("-")[1]
    year = minutes_name[5:9]
    month = minutes_name[1:3]
    day = minutes_name[3:5]

    new_name = f"{year}_{month}_{day}_minutes_{doc_id}.pdf"

    meeting_folder = MINUTES_FOLDER.joinpath(container_name, meeting_name)
    meeting_folder.mkdir(exist_ok=True, parents=True)

    file_path = meeting_folder.joinpath(new_name)
    if file_path.exists():
        return

    minutes_doc = session.get(minutes_url, headers={"User-Agent": USER_AGENT})
    if not minutes_doc.ok:
        print(
            "Error retrieving minutes document:",
            meeting_name,
            minutes_name,
            minutes_doc.reason,
        )
        return

    print(date_header.strong.get_text() + " " + date_header.p.get_text().strip())

    with open(file_path, "wb") as outfile:
        outfile.write(minutes_doc.content)

def get_years(agenda_container: Tag) -> list[str]:
    """Find all the list items that define which years are available to filter on.

    Args:
        agenda_container (Tag): HTML DOM object that contains the year list.

    Returns:
        list[str]: List of year strings.
    """
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
        container_name = (container.find("h2", tabindex="0").text).replace(' ','_')[1:]
        agenda_table_id = re.sub(
            r"[a-zA-Z]",
            "",
            container.find("table", summary="List of Agendas").get("id"),
        )

        for year in year_list:
            payload = {"year": year, "catID": agenda_table_id}
            agendas = session.post(
                URL_UPDATE_AGENDAS, headers={"User-Agent": USER_AGENT}, data=payload
            )
            new_doc = BeautifulSoup(agendas.text, "html.parser")
            rows = new_doc.find_all("tr", class_="catAgendaRow")
            for row in rows:
                process_row_documents(row=row, session=session, container_name=container_name)

def clean_name(input_string: str) -> str:
    """Use regex to replace non-alphanumeric characters with underscores

    Args:
        input_string (str): String to clean and format, such as a meeting title._

    Returns:
        str: Formatted string.
    """
    # TODO: This is a little messy and leaves some errant "_" at the end of some folders.
    input_string = RE_ALPHA.sub("", input_string)
    result_string = (
        RE_ALPHNUM.sub("_", input_string).replace("__", "_").replace("__", "_")
    )
    return result_string


def is_year(input_string: str) -> bool:
    """Is the input string a 4-digit number?

    Args:
        input_string (str): String to evaluate

    Returns:
        bool: Well is it?
    """
    year = re.compile(r"\d{4}")
    return True if year.match(input_string) else False
