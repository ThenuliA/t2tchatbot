

# This file handles reading and writing the cached knowledge, so writing the scraped data
# also reads the data in the file and returns them
# handles checking date and checking whether file was created that day
from datetime import datetime

CACHE_FILE = "t2t_knowledge.txt"
DATE_FORMAT = "%Y-%m-%d"
DATE_PREFIX = "DATE: "
WEBSITE_HEADER = "===WEBSITE DATA==="
EVENTS_HEADER = "===EVENTS DATA==="


''' file format is
    DATE: YYYY-MM-DD
    ===WEBSITE DATA===
    <scraped website content>
    ===EVENTS DATA===
    <formatted events content>
'''
def get_today_str():  # returns the currect date
    return datetime.now().strftime(DATE_FORMAT)


def write_cache(website_content: str, events_text: str):
    """Write scraped data to the cache file with today's date at the top."""
    today = get_today_str()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(f"{DATE_PREFIX}{today}\n")
        f.write(f"{WEBSITE_HEADER}\n") 
        f.write(website_content)
        f.write(f"\n{EVENTS_HEADER}\n")
        f.write(events_text)
        # writes date, ==WEBSITE DATA== and then the data in the website, and event header and data
        # its split into website data and events data because i wanted to put some focus on events as well
    print(f"Cache written to '{CACHE_FILE}' for date {today}.")


def read_cache():
    """
    Read the cache file and return (website_content, events_text).
    Returns (None, None) if file doesn't exist or is malformed.
    """
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")  # splits into lines
        if not lines[0].startswith(DATE_PREFIX): # date is not there in the first row
            print("Cache file is malformed (missing date header).")
            return None, None

        # Split on section headers
        website_start = content.find(WEBSITE_HEADER) # returns -1 if those words arent found in file
        events_start = content.find(EVENTS_HEADER)

        if website_start == -1 or events_start == -1:  
            print("Cache file is malformed (missing section headers).")
            return None, None

        website_content = content[website_start + len(WEBSITE_HEADER):events_start].strip() # gets data from start of website data until events
        events_text = content[events_start + len(EVENTS_HEADER):].strip()  # gets event data

        return website_content, events_text

    except FileNotFoundError:
        return None, None


def get_cache_date():
    """
    Return the date string stored in the cache file, or None if not found.
    """
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if first_line.startswith(DATE_PREFIX):
            return first_line[len(DATE_PREFIX):]
        return None
    except FileNotFoundError:
        return None


def is_cache_fresh():
    """
    Returns True if the cache file exists and was written today.
    """
    cached_date = get_cache_date()
    if cached_date is None:
        return False
    return cached_date == get_today_str()  # returns a boolean