import requests
import json

def search_hiking_in_spatial():
    print("Searching for hiking trails in SpatialData...")
    url = "https://tourism.api.opendatahub.com/v1/SpatialData"
    params = {
        "pagesize": 5,
        "tagfilter": "hikingtrails"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("Items", [])
        print(f"Found {len(items)} items with tag 'hikingtrails' in SpatialData")
        if items:
            with open("spatial_hiking_sample.json", "w") as f:
                json.dump(items[0], f, indent=2)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_hiking_in_spatial()
