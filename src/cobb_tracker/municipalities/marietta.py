import requests
import logging
import re

from cobb_tracker import file_ops
from cobb_tracker.cobb_config import CobbConfig


from bs4.element import Tag
from bs4 import BeautifulSoup

URL_BASE = "https://www.mariettaga.gov"
URL_AGENDAS = f"{URL_BASE}/AgendaCenter"
URL_UPDATE_AGENDAS = f"{URL_BASE}/AgendaCenter/UpdateCategoryList"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)

RE_ALPHNUM = re.compile(r"[^a-zA-Z0-9]")
RE_ALPHA = re.compile(r"[0-9\.\-]")


def name_documents(
    session: requests.Session,
    container_name: str,
    config: CobbConfig,
    minutes_urls: dict,
) -> None:
    """Parse meeting information and documents from a table row.

    Args:
        row (Tag): Row from a Marietta meeting list table.
        session (requests.Session): Session object for doing HTTP calls.
    """
    for url in minutes_urls.keys():
        row = minutes_urls[url]
        meeting_title = row.find("a", {"aria-describedby": True}, target="_blank")
        if meeting_title is None:
            return
        minutes_urls[url]["meeting_name"] = clean_name(
            meeting_title.text.strip().title()
        )
        minutes_urls[url]["municipality"] = "Marietta"
        minutes_urls[url]["file_type"] = "minutes"

        minutes_name = url.split("/")[-1]

        year = minutes_name[5:9]
        month = minutes_name[1:3]
        day = minutes_name[3:5]

        minutes_urls[url]["date"] = f"{year}-{month}-{day}"

    doc_ops = file_ops.FileOps(
        session=session, user_agent=USER_AGENT, file_urls=minutes_urls, config=config
    )
    doc_ops.write_minutes_doc()


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


def get_minutes_docs(config: CobbConfig):
    minutes_urls = {}
    session = requests.Session()

    response = session.get(URL_AGENDAS, headers={"User-Agent": USER_AGENT})
    if not response.ok:
        logging.error("Request failed:", response.reason, response.status_code)
        return

    soup = BeautifulSoup(response.content, "html.parser")
    agenda_containers = soup.find_all("div", class_="listing listingCollapse noHeader")
    for container in agenda_containers:
        year_list = get_years(container)
        container_name = (container.find("h2", tabindex="0").text).replace(" ", "_")[1:]
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
                minutes = row.find("td", class_="minutes")
                minutes_link = minutes.find("a")
                if minutes_link:
                    minutes_url = f"{URL_BASE}{minutes_link.get('href')}"
                    minutes_urls[minutes_url] = row

    name_documents(
        minutes_urls=minutes_urls,
        session=session,
        container_name=container_name,
        config=config,
    )


def clean_name(input_string: str) -> str:
    """Use regex to replace non-alphanumeric characters with underscores

    Args:
        input_string (str): String to clean and format, such as a
        meeting title._

    Returns:
        str: Formatted string.
    """
    # TODO:
    # This is a little messy and leaves some errant "_" at
    # the end of some folders.
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
