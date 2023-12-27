import fitz
import sys
import pytesseract

from PIL import Image
from sqlite_utils import Database
from sqlite_utils import db
import io

from pathlib import Path
import os
from multiprocessing import Process
from multiprocessing import Semaphore

import shutil
import numpy as np

from cobb_tracker import file_ops
import math
from cobb_tracker.cobb_config import CobbConfig

class DatabaseOps():
    def __init__(self, config: CobbConfig):
        """
            Args:
                congig(CobbConfig) Object that contains the user's configuration settings.
        """
        self.SEMAPHORE = Semaphore(len(os.sched_getaffinity(0)))
        self.DATABASE_DIR=config.get_config("directories","database_dir")
        self.MINUTES_DIR=config.get_config("directories","minutes_dir")
        self.DB = Database(os.path.join(self.DATABASE_DIR,"minutes.db"))

        self.args = config.get_args()

        self.doc_ops = file_ops.FileList(minutes_dir=config.get_config("directories","minutes_dir"))
        self.config = config
        self.mins_and_checksums = {}

        tesseract_location = shutil.which('tesseract')
        
        if tesseract_location is not None:
            pytesseract.pytesseract.tesseract_cmd = tesseract_location
        else:
            print("Error: Tesseract is not in PATH or is not installed")
            sys.exit()


    def pdf_to_database(self):
        config = self.config
        DB = self.DB 
        all_minutes_files = np.array(self.doc_ops.minutes_files())
        doc_ops = file_ops.FileList(minutes_dir=self.MINUTES_DIR)

        all_minutes_files = np.array(doc_ops.minutes_files())
        if len(all_minutes_files) == 0:
            print(f"Error: There are no minutes files in {self.MINUTES_DIR}!")
            return

        if not DB["pages"].exists():
            DB["pages"].create(
                    { "municipality": str,
                      "body": str,
                      "date": str,
                      "page": int,
                      "text": str,
                      "checksum": str
                     },
                pk=( "municipality","body", "date", "page", "checksum"),
            )
            DB["pages"].enable_fts(["text"], create_triggers=True)


        batches = math.ceil(len(all_minutes_files)/300)
        array_of_all_minutes_files = np.array_split(all_minutes_files, batches)

        for list_of_minutes_files in array_of_all_minutes_files:
            db_processes = [Process(target=self.write_to_database,args=(file,)) for file in list_of_minutes_files]
            for process in db_processes:
                process.start()
            for process in db_processes:
                process.join()

    def write_to_database(self,minutes_file: str):
        with self.SEMAPHORE:
            DB = self.DB
            config = self.config
            checksum = str(self.doc_ops.get_checksum(Path(minutes_file)))

            # Must zoom in in order for tesseract to give mostly accurate transcription
            ZOOM = 2
            MAT = fitz.Matrix(ZOOM, ZOOM)
            file = str(minutes_file)
            
            try:
                doc = fitz.open(file)

            except Exception as e:
                print(f"Error: {e} {file}")
                return

            rel_doc_path=file.replace(config.get_config('directories','minutes_dir'),'')
            municipality = os.path.normpath(rel_doc_path).split(os.path.sep)[1].replace('_',' ')
            body = os.path.normpath(rel_doc_path).split(os.path.sep)[2].replace('_',' ')
            date = (os.path.split(Path(file))[1]).replace('-minutes.pdf','')
            checksum_row_count = sum(1 for row in DB.query(f"select * from pages where checksum = '{checksum}'"))

            if checksum_row_count == 0 or self.args.force:
                print(checksum)
                print(f"{file}")
                for page in doc:
                    pix = page.get_pixmap(matrix=MAT)
                    image_bytes = io.BytesIO(
                                pix.tobytes(output="jpeg", jpg_quality=98)
                            )
                    page_image = Image.open(image_bytes)
                    page_text = pytesseract.image_to_string(page_image)
                    page_image.close()
                    DB["pages"].insert(
                        {
                            "municipality": municipality,
                            "body": body,
                            "date": date,
                            "page": page.number,
                            "text": page_text,
                            "checksum": checksum,

                        },
                        replace=True,
                    )
            doc.close()
