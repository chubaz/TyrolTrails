import requests
import json
import time

BASE_URL = "https://tourism.api.opendatahub.com/v1/SpatialData"

def fetch_and_save_all_data(output_file="spatialdata_all.json", tag_filter=None):
    all_items = []
    current_page = 1
    total_pages = 1  # This will be updated after the first request

    print(f"Starting data fetch from {BASE_URL}...")
    if tag_filter:
        print(f"Applying filter for tag: {tag_filter}")

    while current_page <= total_pages:
        # Build query parameters
        params = {
            "pagenumber": current_page,
            "pagesize":1000,
            "removenullvalues": "true"
        }
        # If you are continuing with a specific tag from Task 1, uncomment this in usage
        if tag_filter:
            params["tagfilter"] = tag_filter

        try:
            print(f"Fetching page {current_page} of {total_pages if total_pages > 1 else '?'}...")
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # --- Task 2b: Read TotalPages on the first run ---
            if current_page == 1:
                total_pages = data.get("TotalPages", 1)
                total_results = data.get("TotalResults", 0)
                print(f"Total results to fetch: {total_results}")
                print(f"Total pages to process: {total_pages}\n")
            
            items = data.get("Items", [])
            
            # --- Task 2a: Print the requested fields ---
            # We'll print the fields for the first few items so we don't flood the console
            if current_page == 1 and items:
                print("--- Task 2a: Preview of First Page Records ---")
                for item in items[:5]: # Showing top 5 as an example
                    item_id = item.get("Id")
                    source = item.get("Source", "Unknown")
                    meta_type = item.get("_Meta", {}).get("Type", "Unknown")
                    
                    # Safely extract title from Detail in any available language
                    title = "No Title Found"
                    detail = item.get("Detail", {})
                    if detail:
                        # Try English or German first, then fallback to whatever is available
                        for lang in ['en', 'de', 'it', 'nl']:
                            if lang in detail and 'Title' in detail[lang]:
                                title = detail[lang]['Title']
                                break
                        # Fallback if preferred languages are missing
                        if title == "No Title Found":
                            for lang, content in detail.items():
                                if isinstance(content, dict) and 'Title' in content:
                                    title = content['Title']
                                    break
                    
                    print(f"ID: {item_id}")
                    print(f"Source: {source} | Type: {meta_type}")
                    print(f"Title: {title}")
                    print("-" * 40)
                print("\nContinuing to fetch remaining pages in the background...\n")

            # Collect every item into our single list
            all_items.extend(items)
            current_page += 1
            
            # A tiny sleep to be polite to the Open Data Hub servers
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {current_page}: {e}")
            break

    # --- Task 2b: Save all collected items locally ---
    print(f"\nFinished fetching! Total records collected: {len(all_items)}")
    print(f"Saving flat array to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Saving as a flat JSON array of objects
        json.dump(all_items, f, ensure_ascii=False, indent=2)
        
    print(f"Success! Data saved to {output_file}")

if __name__ == "__main__":
    # If you want to download EVERYTHING (10,000+ records), leave tag_filter=None. 
    # If you want to filter based on your findings in Task 1, add it here (e.g., tag_filter="mtb").
    fetch_and_save_all_data(output_file="spatialdata_all.json", tag_filter=None)