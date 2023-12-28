import dateutil.parser
import re
def parse_date(raw_date: str):
    try:
        filtered_date = dateutil.parser.parse(re.sub(r'([a-z]{1})(\d)',r'\1 \2',raw_date))
        return filtered_date.strftime("%Y-%m-%d")
    except:
        return "Unknown"
