"""
This module handles the conversion of PDFs to
text, as well as the operations for putting this text
into the database
"""
import sys
import io
import os
import logging
from pathlib import Path
import requests
from multiprocessing import Process
from multiprocessing import Semaphore
import shutil
import math
import time

import numpy as np

from cobb_tracker import file_ops
from cobb_tracker.cobb_config import CobbConfig


class PaperlessOps:
    def __init__(self, config: CobbConfig):
        """
        Args:
            config(CobbConfig) Object that contains the user's
            configuration settings.
        """
        self.SEMAPHORE = Semaphore(len(os.sched_getaffinity(0)))
        self.MINUTES_DIR = config.get_config("directories", "minutes_dir")

        #Paperless-ngx credentials provided by users
        self.PAPERLESS_URL = config.get_config("paperless-config", "paperless_url")
        self.PAPERLESS_TOKEN = config.get_config("paperless-config", "paperless_token")
        self.HEADERS = {'Authorization': 'token {}'.format(self.PAPERLESS_TOKEN)}

        self.args = config.args
        self.doc_ops = file_ops.FileList(
            minutes_dir=config.get_config("directories", "minutes_dir")
        )
        self.config = config
        self.mins_and_checksums = {}

    def pdf_to_paperless(self):
        all_minutes_files = np.array(self.doc_ops.minutes_files())
        doc_ops = file_ops.FileList(minutes_dir=self.MINUTES_DIR)

        all_minutes_files = np.array(doc_ops.minutes_files())
        if len(all_minutes_files) == 0:
            logging.error(f"There are no minutes files in {self.MINUTES_DIR}!")
            return

        batches = math.ceil(len(all_minutes_files) / 300)
        array_of_all_minutes_files = np.array_split(all_minutes_files, batches)

        for list_of_minutes_files in array_of_all_minutes_files:
            upload_processes = [
                Process(target=self.upload_to_paperless, args=(file,))
                for file in list_of_minutes_files
            ]
            for process in upload_processes:
                process.start()
            for process in upload_processes:
                process.join()

    def upload_to_paperless(self, minutes_file: str):
        """
            The PDFs are sent to paperless ngx. Provide the URL and the Token
        """
        with self.SEMAPHORE:
            file = str(minutes_file)

            rel_doc_path = file.replace(
                self.config.get_config("directories", "minutes_dir"), ""
            )
            municipality = (
                os.path.normpath(rel_doc_path)
                .split(os.path.sep)[1]
                .replace("_", " ")
            )
            body = (
                os.path.normpath(rel_doc_path)
                .split(os.path.sep)[2]
                .replace("_", " ")
            )
            date = (os.path.split(Path(file))[1]).replace("-minutes.pdf", "")

            files = {
                "document": (minutes_file, open(minutes_file, 'rb'), "application/pdf"),
            }
            data = {
                "created": date,
                "document": open(minutes_file,'rb'),
                "title": f"{body} minutes",
                "from_webui": False,
            }

            post_document=f"{self.PAPERLESS_URL}/api/documents/post_document/"
            print(post_document)
            time.sleep(3)
            response = requests.post(post_document, headers=self.HEADERS, files=files, data=data)
            print(response.content)
