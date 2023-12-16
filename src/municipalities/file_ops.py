import pathlib
import sys
import os
import asyncio
import requests

async def write_minutes_doc(
            doc_date: str, 
            meeting_type: str,
            file_url: str,
            pdf_path: pathlib.Path,
            municipality: str
        ):
    """Download and write minutes file for the specified meeting to disk
    
    Args:
        doc_date (str): The date the event took place in the format YYYY-MM-D   
        meeting_type (str): What type of meeting was this?
        file_url (str): Where is this file locatied?
        pdf_path (pathlib.Path): Where do you want this file to be written to?
        municipality (str): This will either be Cobb County or one of it's cities.
    """

    pdf_file = requests.get(file_url).content
    pdf_path.mkdir(parents=True, exist_ok=True)
    meeting_type = meeting_type.lower()
    with open(pdf_path.joinpath(f"{doc_date}-{meeting_type}.pdf"), "wb") as file:
        file.write(pdf_file)
