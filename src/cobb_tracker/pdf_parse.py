import fitz
import sys
import pytesseract
from PIL import Image
from sqlite_utils import Database
import io

def write_to_database(minutes_dir: str, database_dir: str):
    doc = fitz.open(f"{minutes_dir}/Cobb/BOC_Zoning_Hearing/2023-11-21-minutes.pdf")
    pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

    # Must zoom in in order for tesseract to give accurate transcription
    ZOOM = 2
    MAT = fitz.Matrix(ZOOM, ZOOM)
    DB = Database("minutes.db")

    if not DB["pages"].exists():
        DB["pages"].create(
            {"body": str, "date": str, "page": int, "text": str},
            pk=("body", "date", "page"),
        )
        DB["pages"].enable_fts(["text"], create_triggers=True)

    for page in doc:
        pix = page.get_pixmap(matrix=MAT)
        image_bytes = io.BytesIO(
                    pix.tobytes(output="jpeg", jpg_quality=98)
                )
        page_text = pytesseract.image_to_string(Image.open(image_bytes))
        DB["pages"].insert(
            {
                "body": "BOC Zoning Commission",
                "date": "2023-11-21",
                "page": page.number,
                "text": page_text,

            },
            replace=True,
        )
