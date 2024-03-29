import re
import dateutil


def parse_date(raw_date: str):
    filtered_date = dateutil.parser.parse(
        re.sub(r"([a-z]{1})(\d)", r"\1 \2", raw_date)
    )
    return filtered_date.strftime("%Y-%m-%d")
