# config.py

# Webex API details
ACCESS_TOKEN = "ODVkNzkyODgtMjc3Ni00NjkzLWEzZTUtNTA4Y2JkYmQxODQ5NTU5YWVjYmUtMjUw_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
MAX_RESULTS = 50  # Number of messages per request

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