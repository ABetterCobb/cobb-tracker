import subprocess
import re
import shutil
import time
import logging


import sys
from datetime import datetime
from cobb_tracker.string_ops import parse_date

import requests
from cobb_tracker.file_ops import FileOps
from cobb_tracker.cobb_config import CobbConfig

from selenium.common.exceptions import ElementNotInteractableException
from selenium import webdriver
import signal

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


def signal_handler(signal, frame):
    subprocess.run(["sudo", "docker", "rm", "-f", "selenium"],
                   stdout=subprocess.DEVNULL)
    sys.exit(0)


def get_minutes_docs(config: CobbConfig):
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )
    signal.signal(signal.SIGINT, signal_handler)
    docker_location = shutil.which('docker')
    if docker_location is None:
        logging.error("Docker is not in PATH or not installed")
        sys.exit()

    if sys.platform.startswith('linux'):

        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
            subprocess.run(['sudo', 'docker', 'run',
                            '-p', '4444:4444',
                            '-p', '7900:7900',
                            '--rm',
                            '-d',
                            '--name', 'selenium',
                            '-it', 'selenium/standalone-chrome:latest'])
        except Exception as e:
            logging.error(f"{e}")
            sys.exit()

    elif sys.platform.startswith('darwin'):
        try:
            subprocess.run(['docker', 'run',
                            '-p', '4444:4444',
                            '-p', '7900:7900',
                            '--rm',
                            '-d',
                            '--name', 'selenium',
                            '-it', 'selenium/standalone-chrome:latest'])

        except Exception as e:
            logging.error(f"{e}")
            sys.exit()
    else:
        logging.error(f"Unsupported platform {sys.platform}")

    time.sleep(5)
    browser = webdriver.Remote(command_executor="http://localhost:4444", options=webdriver.ChromeOptions())
    try:
        browser.get("https://kennesaw.novusagenda.com/agendapublic")

        time.sleep(5)
        drop_down = Select(browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_SearchAgendasMeetings_ddlDateRange"))
        drop_down.select_by_visible_text("Custom Date Range")
        time.sleep(2)

        start_date = browser.find_element("id","ctl00_ContentPlaceHolder1_SearchAgendasMeetings_radCalendarFrom_dateInput")
        start_date.clear()
        start_date.send_keys("1/1/2000")

        start_date = browser.find_element("id","ctl00_ContentPlaceHolder1_SearchAgendasMeetings_radCalendarTo_dateInput")
        start_date.clear()
        start_date.send_keys(datetime.strftime(datetime.now(),"%m/%d/%Y"))

        search = browser.find_element("id","ctl00_ContentPlaceHolder1_SearchAgendasMeetings_imageButtonSearch")
        search.click()
        time.sleep(6)
        minutes_urls = {}

        minutes_row_reg = re.compile(r'ctl00_ContentPlaceHolder1_SearchAgendasMeetings_radGridMeetings_ctl00.*')
        minutes_link_reg = re.compile(r'ctl00_ContentPlaceHolder1_SearchAgendasMeetings_radGridMeetings.*hypMinutesPDF')

            
        while True:
            time.sleep(7)
            all_rows = [ row for row in browser.find_elements(By.TAG_NAME, "tr") if minutes_row_reg.search(row.get_attribute("id")) ]
            for row in all_rows:
                columns = [ column.text for column in row.find_elements(By.TAG_NAME,"td") if (column.text != '' and
                                                                                '\n' not in column.text)]
                #delete meeting location
                del columns[-1]
                
                link = [ minutes_link.get_attribute("href") for minutes_link in row.find_elements(By.TAG_NAME,'a') if minutes_link_reg.search(minutes_link.get_attribute("id")) ] 

                if len(link) > 0:
                    columns.append(link[0])
                else:
                    columns.append(None)

                if columns[2] is not None:
                    file_url = columns[2]
                    minutes_urls[file_url] = {}
                    minutes_urls[file_url]["municipality"] = "Kennesaw"
                    minutes_urls[file_url]["meeting_name"] = columns[1]
                    minutes_urls[file_url]["date"] = parse_date(columns[0])
                    minutes_urls[file_url]["file_type"] = "minutes" 

            next_button = "//td[contains(@class, 'rgPagerCell NextPrevAndNumeric')]//div[contains(@class, 'rgWrap rgArrPart2')]/a[@href]"
            link = browser.find_element(By.XPATH,next_button)
            try:
                link.click()
            except ElementNotInteractableException:
               break 
    finally:
        browser.quit()

    if sys.platform.startswith('linux'):
        subprocess.run(["sudo", "docker", "rm", "-f", "selenium"],
                       stdout=subprocess.DEVNULL) 
    elif sys.platform.startswith('darwin'):
        subprocess.run(["docker", "rm", "-f", "selenium"],
                       stdout=subprocess.DEVNULL) 

        session = requests.Session()
        doc_ops = FileOps(
                file_urls=minutes_urls,
                session=session,
                user_agent=USER_AGENT,
                config=config
               )
        doc_ops.write_minutes_doc()
