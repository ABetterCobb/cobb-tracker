import pathlib
import sys
import os
import asyncio
import requests

async def write_minutes_doc(
            doc_date: str, 
            file_type: str,
            file_url: str,
            pdf_path: pathlib.Path,
            municipality: str
        ):
    pdf_file = requests.get(file_url).content
    pdf_path.mkdir(parents=True, exist_ok=True)
    file_type = file_type.lower()
    with open(pdf_path.joinpath(f"{doc_date}-{file_type}.pdf"), "wb") as file:
        file.write(pdf_file)
