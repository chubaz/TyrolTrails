import requests
from ingest_data import parse_single_trail

api_url = "https://tourism.api.opendatahub.com/v1/ODHActivityPoi?pagenumber=1&pagesize=10&type=255"
response = requests.get(api_url)
items = response.json().get('Items', [])

for item in items:
    parsed = parse_single_trail(item)
    if parsed:
        print(f"ID: {parsed['track_id']}, Name: {parsed['name']}, Length: {parsed['length_m']}, Elevation: {parsed['elevation_up_m']}")
    else:
        print(f"ID: {item.get('Id')} failed to parse")
