#!/usr/bin/env python
import docker
import subprocess
import sys
import re

import signal
import time

from datetime import datetime
from cobb_tracker.string_ops import parse_date 

import requests
from cobb_tracker.municipalities.file_ops import FileOps
from cobb_tracker.cobb_config import CobbConfig

from selenium.common.exceptions import ElementNotInteractableException
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

def get_minutes_docs(config: CobbConfig):
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )
    client = docker.from_env()
    try:
        client.containers.run("selenium/standalone-chrome:latest",
                              ports={4444:4444,7900:7900},
                              shm_size="2G",
                              name="selenium",
                              detach=True,
                              auto_remove=True
                              )
    except Exception as e:
        print(f"Error {e}")

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
        pages_num = browser.find_element(By.XPATH, "/html/body/form/div[4]/div[2]/div[3]/span/table/tbody/tr[3]/td/div[3]/div[1]/div[1]/div/div/table/tfoot/tr/td/table/tbody/tr/td/div[5]").text
        minutes_links = []
        minutes_urls = {}
        get_page_num = r'( \d.* items in )|( pages)'
        page_num = int(re.sub(get_page_num,'',pages_num))

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

                if columns[2] != None:
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

    session = requests.Session()
    doc_ops = file_ops.FileOps(
            file_urls=minutes_urls,
            session=session,
            user_agent=self.USER_AGENT,
            config=config
           )
    doc_ops.write_minutes_doc()

subprocess.run(["docker", "rm", "-f", "selenium"],
               stdout=subprocess.DEVNULL) 
