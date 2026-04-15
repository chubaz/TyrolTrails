import os
from dotenv import load_dotenv
import requests
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Database connection
engine = create_engine(DATABASE_URL)

def parse_measuring_point(item):
    item_id = item.get('Id')
    
    # 1. Try fetching coordinates from the root
    lat = item.get('Latitude')
    lon = item.get('Longitude')
    
    # 2. Fallback to the GpsInfo array if root is empty
    if not lat or not lon:
        gps_info = item.get('GpsInfo', [])
        if gps_info:
            lat = gps_info[0].get('Latitude')
            lon = gps_info[0].get('Longitude')
            
    if lat and lon:
        return {
            'id': item_id,
            'name': item.get('Shortname') or f"Station {item_id}",
            'temperature': item.get('Temperature'), # Will default to None if missing
            'latitude': lat,
            'longitude': lon
        }
    return None

def ingest_weather():
    poi_list = []
    page = 1
    endpoint = 'Weather/Measuringpoint'
    table_name = 'measuring_points'
    
    print(f"\n--- Fetching Weather Measuring Points from API ---")
    while True:
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
                    parsed_item = parse_measuring_point(item)
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
        print("No valid weather records found.")
        return

    df = pd.DataFrame(poi_list)
    df = df.drop_duplicates(subset=['id'])
    
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )
    
    print(f"Saving {len(gdf)} unique stations to PostGIS table '{table_name}'...")
    gdf.to_postgis(table_name, engine, if_exists='replace', index=False)
    print(f"Success! {table_name} saved.")

if __name__ == "__main__":
    ingest_weather()
