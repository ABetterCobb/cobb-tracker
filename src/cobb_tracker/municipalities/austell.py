
import requests
import re
import os
import sys

from autocorrect import Speller
import dateutil.parser

from cobb_tracker.municipalities import file_ops
from cobb_tracker.cobb_config import CobbConfig

from bs4.element import Tag
from bs4 import BeautifulSoup

URL_BASE = "https://www.austellga.gov/"
CURRENT_MINUTES = f"{URL_BASE}AgendasandMinutes.aspx"
PREVIOUS_MINUTES = f"{URL_BASE}PastAgendasandMinutes.aspx"
#FILE_PAGE = f"{LIST_OF_ARCHIVE_SECTIONS}?ADID="
minutes_urls = {}
muni = "Austell"
session = requests.Session()


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )
def get_minutes_docs(config: CobbConfig):
    archive_groups = {} 
    response = session.get(CURRENT_MINUTES, headers={"User-Agent": USER_AGENT})

    if not response.ok:
        print("Request failed:", response.reason, response.status_code)
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    print(soup.text)
