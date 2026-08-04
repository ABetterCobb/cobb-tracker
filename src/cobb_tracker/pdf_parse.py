"""
This module handles the conversion of PDFs to
text, as well as the operations for putting this text
into the database
"""
import sys
import io
import os
import logging
import re
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

    def get_document_type(self, doc_type: str):
        doc_type_url = f"{self.PAPERLESS_URL}/api/document_types/"
        doc_type_query = f"{doc_type_url}?name__iexact={doc_type}"
        response = requests.get(doc_type_query, headers=self.HEADERS).json()

        return response["results"][0]["id"]
    def doc_exists(self, checksum: str):
        docs_url = f"{self.PAPERLESS_URL}/api/documents/"
        doc_query = f"{docs_url}?checksum__iexact={checksum}"
        response = requests.get(doc_query, headers=self.HEADERS).json()
        
        if response["count"] == 0:
            return False
        else:
            return True

    def get_tag(self, tag: str):
        tag_url = f"{self.PAPERLESS_URL}/api/tags/"
        tag_query = f"{tag_url}?name__iexact={tag}"
        response = requests.get(tag_query, headers=self.HEADERS).json()
        
        if response["count"] == 0:
            return None
        return response["results"][0]["id"]

    def set_tag(self, tag: str):
        tag_url = f"{self.PAPERLESS_URL}/api/tags/"
        data = {
            "name": tag,
            "owner": 1
        }
        response = requests.post(tag_url, headers=self.HEADERS, data=data)


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
            checksum = str(self.doc_ops.get_checksum(Path(minutes_file)))
            if not self.doc_exists(checksum):
                post_document=f"{self.PAPERLESS_URL}/api/documents/post_document/"
                correspondents=f"{self.PAPERLESS_URL}/api/correspondents/"
                doc_types=f"{self.PAPERLESS_URL}/api/document_types/"
                file = str(minutes_file)

                rel_doc_path = file.replace(
                    self.config.get_config("directories", "minutes_dir"), ""
                )
                municipality = (
                    os.path.normpath(rel_doc_path)
                    .split(os.path.sep)[1]
                    .replace("_", " ")
                )

                #Set correspondent to municipality
                muni_query=f"{correspondents}?name__iexact={municipality}"
                muni_correspondent = requests.get(muni_query, headers=self.HEADERS).json()

                if muni_correspondent["count"] == 0:
                    data = {
                        "name": municipality,
                        "owner": 1
                    }
                    response = requests.post(correspondents, headers=self.HEADERS, data=data)

                muni_correspondent = requests.get(muni_query, headers=self.HEADERS).json()
                muni_corr_id = muni_correspondent["results"][0]["id"]

                #Get Committee/Body
                body = (
                    os.path.normpath(rel_doc_path)
                    .split(os.path.sep)[2]
                    .replace("_", " ")
                )
                if self.get_tag(body) is None:
                    self.set_tag(body)
                 
                #Set document type
                if "minutes" in os.path.split(Path(file))[1]:
                    doc_type = "Minutes"

                doc_type_query = f"{doc_types}?name__iexact={doc_type}"
                document_type = requests.get(doc_type_query, headers=self.HEADERS).json()
                if document_type["count"] == 0:
                    data = {
                        "name": doc_type,
                        "owner": 1
                    }
                    response = requests.post(doc_types, headers=self.HEADERS, data=data)


                #Post file
                match = re.match(r"(\d{4}-\d{2}-\d{2})", (os.path.split(Path(file))[1]))

                date = match.group(1)
                
                with open(minutes_file, "rb") as f:
                    files = {
                        "document": (os.path.basename(minutes_file), f, "application/pdf"),
                    }

                    data = {
                        "created": date,
                        #"document": open(minutes_file,'rb'),
                        "document_type": self.get_document_type(doc_type), 
                        "title": f"{body} minutes",
                        "tags": [self.get_tag(body)],
                        "correspondent": muni_corr_id,
                    }

                    post_document=f"{self.PAPERLESS_URL}/api/documents/post_document/"
                    time.sleep(1.5)
                    response = requests.post(post_document, headers=self.HEADERS, files=files, data=data)

                    if not response.ok:
                        print(response.content, date, minutes_file, data)
