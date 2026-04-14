import os
from dotenv import load_dotenv
import requests
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Database connection with pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

def fetch_and_save_dataset(endpoint, table_name, parse_function):
    """A generic function to handle pagination and saving for any ODH endpoint."""
    poi_list = []
    page = 1
    
    print(f"\n--- Fetching ALL {table_name.upper()} from API ---")
    while True:
        # ODHActivityPoi has a different base path than the others sometimes, but usually /v1/ works.
        api_url = f"https://tourism.api.opendatahub.com/v1/{endpoint}?pagenumber={page}&pagesize=1000"
        
        try:
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()
            items = data.get('Items', [])
            
            if not items:
                print(f"   Finished fetching. Total items: {len(poi_list)}")
                break

            for item in items:
                try:
                    parsed_item = parse_function(item)
                    if parsed_item:
                        poi_list.append(parsed_item)
                except Exception:
                    continue
            
            print(f"   Fetched page {page}...")
            page += 1
        except Exception as e:
            print(f"   Error fetching page {page}: {e}")
            break
            
    if not poi_list:
        print(f"No valid records found for {table_name}.")
        return

    # Deduplication and GeoDataFrame creation
    df = pd.DataFrame(poi_list)
    df = df.drop_duplicates(subset=['id'])
    
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )
    
    print(f"Saving {len(gdf)} unique {table_name} to PostGIS...")
    gdf.to_postgis(table_name, engine, if_exists='replace', index=False)
    print(f"Success! {table_name} saved.")


# ==========================================
# PARSER FUNCTIONS FOR EACH DOMAIN
# ==========================================

def parse_gastronomy(item):
    item_id = item.get('Id')
    details = item.get('Detail', {})
    detail = details.get('en') or details.get('de') or details.get('it') or {}
    
    lat = item.get('Latitude')
    lon = item.get('Longitude')
    
    if lat and lon:
        return {
            'id': item_id,
            'name': detail.get('Title') or f"Restaurant {item_id}",
            'type': (item.get('GastronomyType') or {}).get('Id'),
            'phone': (item.get('ContactInfos', {}).get('en') or {}).get('Phonenumber'),
            'website': (item.get('ContactInfos', {}).get('en') or {}).get('Url'),
            'image_url': (item.get('ImageGallery', [{}])[0]).get('ImageUrl'),
            'latitude': lat,
            'longitude': lon
        }
    return None

def parse_webcam(item):
    item_id = item.get('Id')
    lat = item.get('Latitude')
    lon = item.get('Longitude')
    
    if lat and lon:
        return {
            'id': item_id,
            'name': item.get('Webcamname', f"Webcam {item_id}"),
            'image_url': item.get('Webcamurl'), # Webcams usually provide the live URL here
            'latitude': lat,
            'longitude': lon
        }
    return None

def parse_event(item):
    item_id = item.get('Id')
    details = item.get('Detail', {})
    detail = details.get('en') or details.get('de') or details.get('it') or {}
    
    lat = item.get('Latitude')
    lon = item.get('Longitude')
    
    if lat and lon:
        return {
            'id': item_id,
            'name': detail.get('Title') or f"Event {item_id}",
            'begin_date': item.get('DateBegin'),
            'end_date': item.get('DateEnd'),
            'website': (item.get('ContactInfos', {}).get('en') or {}).get('Url'),
            'image_url': (item.get('ImageGallery', [{}])[0]).get('ImageUrl'),
            'latitude': lat,
            'longitude': lon
        }
    return None

def parse_poi(item):
    # This fetches general Points of Interest (parking, water, viewpoints)
    item_id = item.get('Id')
    details = item.get('Detail', {})
    detail = details.get('en') or details.get('de') or details.get('it') or {}
    
    # Exclude hiking trails (Type 255) to prevent duplicating what you already have
    poi_type = item.get('Type')
    if poi_type == 255:
        return None 
        
    # Sometimes POIs hide coordinates in GpsInfo array
    lat = item.get('Latitude')
    lon = item.get('Longitude')
    if not lat or not lon:
        gps_info = item.get('GpsInfo', [])
        if gps_info:
            lat = gps_info[0].get('Latitude')
            lon = gps_info[0].get('Longitude')

    if lat and lon:
        return {
            'id': item_id,
            'name': detail.get('Title') or f"POI {item_id}",
            'poi_type': poi_type,
            'sub_type': item.get('SubType'),
            'latitude': lat,
            'longitude': lon
        }
    return None

# ==========================================
# EXECUTE THE PIPELINE
# ==========================================

if __name__ == "__main__":
    print("Starting Rich Data Pipeline...")
    
    # 1. Gastronomy
    fetch_and_save_dataset('Gastronomy', 'gastronomy', parse_gastronomy)
    
    # 2. Webcams
    fetch_and_save_dataset('WebcamInfo', 'webcams', parse_webcam)
    
    # 3. Events
    fetch_and_save_dataset('Event', 'events', parse_event)
    
    # 4. Essential POIs (Water, Parking, Viewpoints, etc.)
    fetch_and_save_dataset('ODHActivityPoi', 'essential_pois', parse_poi)
    
    print("\n🎉 All rich datasets have been successfully saved to PostGIS!")