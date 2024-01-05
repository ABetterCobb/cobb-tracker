import requests
import re

from autocorrect import Speller

from cobb_tracker.municipalities import file_ops
from cobb_tracker.cobb_config import CobbConfig
from cobb_tracker.string_ops import parse_date

from bs4 import BeautifulSoup

URL_BASE = "https://cityofpowdersprings.org/"
LIST_OF_ARCHIVE_SECTIONS = f"{URL_BASE}Archive.aspx"
BASE_FILE_URL = f"{URL_BASE}ArchiveCenter/ViewFile/Item/"
FILE_PAGE = f"{LIST_OF_ARCHIVE_SECTIONS}?ADID="
minutes_urls = {}
muni = "Powder Springs"
session = requests.Session()

'''This expression will try to match many variations of MM/DD/YYYY
The way that Powder Springs stores data means that we're not able
to get information from almost anywhere except the file description.
The dates are in various formats like:
    12.04.23
    12 .04.23
    February 12, 2020
    12.03/22
    12-23-21
all of these will need to be matched since there is no other way to get
that information.
'''
get_year = re.compile(r'((\b(?:(Jan|JAN)(?:uary)?|(FEB|Feb)(?:ruary)?|(Mar|MAR)(?:ch)?|(Apr|APRIL)(?:il)?|(May|MAY)|(Jun|JUNE)(?:e)?|(JULY|Jul)(?:y)?|(AUG|Aug)(?:ust)?|(Sep|Sept|SEPT)(?:tember)?|(OCT|Oct)(?:ober)?|(Nov|NOV|Dec|DEC|DECEMBER)(?:ember)?)\s?(\.|,)?\s?(\d{1,2}\D?)?\D?\s?((19[7-9]\d|20\d{2})))|(\d{1,2}(\.|/|-|,)\s?\d{1,2}(\.|/|-|,)\s?\d{2,4})|([0-1][1-9][0-2][0-9][0-9][0-9])|((JAN|JANUARY)\s{1,2}\d{1,2},\s\d{2}))')

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )
def get_minutes_docs(config: CobbConfig):
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
    get_meeting_info(archive_groups)

    doc_ops = file_ops.FileOps(
        file_urls=minutes_urls,
        session=session,
        user_agent=USER_AGENT,
        config=config
       )
    doc_ops.write_minutes_doc()
    
def get_meeting_info(archive_groups: dict): 
    spell = Speller('en')
    for group in archive_groups.keys():
        if (archive_groups[group] != "Press Releases" and 
            archive_groups[group] != "Town Hall Meetings and Retreats" and
            archive_groups[group] != "City Council Work Session" and
            "Agenda" not in archive_groups[group]):
            group_page = f"{LIST_OF_ARCHIVE_SECTIONS}?AMID={group}&Type=&ADID="
            archive_page_response = session.get(group_page, headers={"User-Agent": USER_AGENT})

            if not archive_page_response.ok:
                print("Request failed:", archive_page_response.reason, archive_page_response.status_code)
                return

            archive_page = BeautifulSoup(archive_page_response.text, 'html.parser')
            '''
            On this "archive_page" , there is a span tag for every link.
            The titles of said links are the only date information
            that is available for these meetings without actually looking
            in the file. The dates are in many different formats, and need
            to be parsed. 

            If a date cannot be parsed, due to a typo or 
            a date just not existing, we check the actual page for the
            individual PDF and see if that has date information. 
            If that doesn't work the file has no date.
            '''

            all_meetings = archive_page.find_all("span", class_="archive")

            for span in all_meetings:
                lines = [ line for line in span.text.split('\n') if line.strip()]
                link = span.find("a")
                name = span.find("span")

                if link is not None and name is not None: 
                    if "agenda" not in name.text.lower():
                        file_id = re.sub(r'[a-zA-Zw\.\?=]','',link.get('href'))
                        file_url = f"{BASE_FILE_URL}{file_id}"

                        minutes_urls[file_url] = {}
                        minutes_urls[file_url]["meeting_name"] = re.sub(r'\s?Minutes','',archive_groups[group]).strip().replace(' ','_')
                        minutes_urls[file_url]["municipality"] = muni
                        minutes_urls[file_url]["file_type"] = "minutes" 

                        date = get_year.search(str(name.text))

                        if date is not None:
                            minutes_urls[file_url]["date"] = parse_date(date.group(0))

                        else:
                            corrected_title = (spell(name.text))
                            date = get_year.search(str(corrected_title))

                            if date is not None:
                                minutes_urls[file_url]["date"] = parse_date(date.group(0))

                            else:
                                singular_page = session.get(f"{FILE_PAGE}{file_id}", headers={"User-Agent": USER_AGENT})

                                if not singular_page.ok:
                                    print("Request failed:", singular_page.reason, singular_page.status_code)
                                    return
                                singular_page_text = BeautifulSoup(singular_page.text, 'html.parser')
                                links = singular_page_text.find_all("a")

                                for link in links:
                                    if link.get("href") is not None:
                                        if "ArchiveCenter" in (link.get("href")):
                                            link_text = link.text
                                            lines = link_text.split('\n')
                                            filtered_link_text = [line for line in lines if line.strip() != '']
                                            date = get_year.search(filtered_link_text[0])

                                            if date is not None:
                                                minutes_urls[file_url]["date"] = parse_date(date.group(0))

                                            else:
                                                minutes_urls[file_url]["date"] = "Date Unknown"
