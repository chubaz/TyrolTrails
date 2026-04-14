import requests
import json

def get_sample(url, name):
    print(f"Fetching sample from {name}...")
    try:
        response = requests.get(url, params={"pagesize": 1}, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("Items", [])
        if items:
            with open(f"sample_{name}.json", "w") as f:
                json.dump(items[0], f, indent=2)
            print(f"Saved sample to sample_{name}.json")
        else:
            print(f"No items found for {name}")
    except Exception as e:
        print(f"Error fetching {name}: {e}")

if __name__ == "__main__":
    get_sample("https://tourism.api.opendatahub.com/v1/SpatialData", "SpatialData")
    get_sample("https://tourism.api.opendatahub.com/v1/ODHActivityPoi?type=255", "ActivityPoi")
