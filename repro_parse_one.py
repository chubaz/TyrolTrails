import requests
from ingest_data import parse_single_trail

api_url = "https://tourism.api.opendatahub.com/v1/ODHActivityPoi/radrouten_tirol_410"
response = requests.get(api_url)
item = response.json()

parsed = parse_single_trail(item)
if parsed:
    print(f"ID: {parsed['track_id']}, Name: {parsed['name']}, Length: {parsed['length_m']}, Elevation: {parsed['elevation_up_m']}")
else:
    print(f"ID: {item.get('Id')} failed to parse")
