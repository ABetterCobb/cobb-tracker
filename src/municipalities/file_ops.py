import pathlib
import sys
import os

def write_minutes_doc(
            doc_date: str, 
            pdf_file: bytes, 
            pdf_path: pathlib.Path,
            municipality: str
        ):
    pdf_path.mkdir(parents=True, exist_ok=True)
    with open(pdf_path.joinpath(f"{doc_date}.pdf"), "wb") as file:
        file.write(pdf_file)
