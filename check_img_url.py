import requests
import json

def get_image_example():
    print("Fetching accommodation image example...")
    url = "https://tourism.api.opendatahub.com/v1/Accommodation"
    params = {"pagesize": 10}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("Items", [])
        for item in items:
            img_gallery = item.get("ImageGallery", [])
            if img_gallery:
                print(f"Name: {item.get('AccoDetail', {}).get('en', {}).get('Name')}")
                print(f"Image URL: {img_gallery[0].get('ImageUrl')}")
                # break # Show only first found
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_image_example()
