import requests
from ingest_data import parse_single_trail

found_elevation = 0
for page in range(1, 6):
    api_url = f"https://tourism.api.opendatahub.com/v1/ODHActivityPoi?pagenumber={page}&pagesize=100&type=255"
    response = requests.get(api_url)
    items = response.json().get('Items', [])
    for item in items:
        parsed = parse_single_trail(item)
        if parsed and parsed['elevation_up_m'] > 0:
            print(f"ID: {parsed['track_id']}, Elevation: {parsed['elevation_up_m']}, Length: {parsed['length_m']}")
            found_elevation += 1
            if found_elevation >= 5: break
    if found_elevation >= 5: break

if found_elevation == 0:
    print("Still no elevation found in first 5 pages of type=255")
