# config.py

import datetime

# Webex API details
ACCESS_TOKEN = "ODVkNzkyODgtMjc3Ni00NjkzLWEzZTUtNTA4Y2JkYmQxODQ5NTU5YWVjYmUtMjUw_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
MAX_RESULTS = 100  # Number of messages per request

# Date range for filtering messages
START_DATE = "01-NOV-2024"  # DD-MMM-YYYY format
END_DATE = "22-MAR-2025"

def format_iso8601(date_str):
    """ Convert 'DD-MMM-YYYY' format to ISO 8601 ('YYYY-MM-DDT00:00:00Z') """
    date_obj = datetime.datetime.strptime(date_str, "%d-%b-%Y")
    return date_obj.strftime("%Y-%m-%dT00:00:00Z")

START_DATE = format_iso8601(START_DATE)
END_DATE = format_iso8601(END_DATE)

ROOMS = {
    "Y2lzY29zcGFyazovL3VzL1JPT00vNmE4NTZhZTAtM2RjZC0xMWVhLWExOTAtYjMzZGMxYmZhY2Zl": "Routing-DATA collaboration",
}


# Webex API URL
BASE_URL = "https://webexapis.com/v1/messages"

# Headers
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "core-team-ai-assistant",
    "user": "core_user",
    "password": "BjqXmDcSWYpUf4J7UY7DKr"
}