import requests
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
from shapely.geometry import shape
from concurrent.futures import ThreadPoolExecutor, as_completed

# Database connection with pooling
engine = create_engine(
    'postgresql://postgres:postgres@localhost:5432/hackathon_db',
    pool_pre_ping=True
)

def parse_single_trail(item):
    """Worker function to download and parse a single trail geometry."""
    track_id = item.get('Id')
    details = item.get('Detail', {})
    name = details.get('en', {}).get('Title') or details.get('de', {}).get('Title') or details.get('it', {}).get('Title') or f"Trail {track_id}"
    length = item.get('DistanceLength', 0)
    elevation_up = item.get('AltitudeSumUp', 0)
    
    gps_track = item.get('GpsTrack')
    if not gps_track or len(gps_track) == 0:
        return None
        
    shape_url = gps_track[0].get('GpxTrackUrl')
    if not shape_url:
        return None

    try:
        shape_response = requests.get(shape_url, timeout=10)
        shape_json = shape_response.json()
        if not shape_json: return None
            
        geom = None
        if 'Geometry' in shape_json and shape_json['Geometry']:
            geom = shape(shape_json['Geometry'])
        elif 'features' in shape_json and len(shape_json['features']) > 0:
             geometry_data = shape_json['features'][0].get('geometry')
             if geometry_data: geom = shape(geometry_data)
        elif 'geometry' in shape_json:
             geom = shape(shape_json['geometry'])
        elif 'type' in shape_json and shape_json['type'] in ['Point', 'LineString', 'Polygon', 'MultiLineString']:
             geom = shape(shape_json)
             
        if geom is None: return None

        return {
            'track_id': track_id,
            'name': name,
            'length_m': length,
            'elevation_up_m': elevation_up,
            'geometry': geom
        }
    except Exception:
        return None

def fetch_and_save_geometries():
    all_items = []
    page = 1
    
    print("1. Fetching ALL trail metadata from API...")
    while True:
        try:
            # Pagination loop
            api_url = f"https://tourism.api.opendatahub.com/v1/ODHActivityPoi?pagenumber={page}&pagesize=1000&type=255"
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()
            items = data.get('Items', [])
            
            if not items:
                print(f"   Finished fetching. Total items: {len(all_items)}")
                break
                
            all_items.extend(items)
            print(f"   Fetched page {page} ({len(all_items)} total items)...")
            page += 1
        except Exception as e:
            print(f"   Error fetching page {page}: {e}. Stopping.")
            break
    
    # Data Deduplication
    print("2. Deduplicating items...")
    unique_items_dict = {item['Id']: item for item in all_items}
    unique_items = unique_items_dict.values()
    print(f"   Unique items found: {len(unique_items)}")

    # Parallel Processing
    results = []
    print("3. Parsing geometries in parallel...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(parse_single_trail, item) for item in unique_items]
        for i, future in enumerate(as_completed(futures)):
            res = future.result()
            if res: results.append(res)
            if i % 100 == 0: print(f"   Progress: {i}/{len(unique_items)}")

    # Save to Database
    if results:
        gdf = gpd.GeoDataFrame(results, crs="EPSG:4326")
        # Final explicit drop to prevent graph corruption
        gdf = gdf.drop_duplicates(subset=['track_id'])
        
        print(f"4. Saving {len(gdf)} unique trails to PostGIS...")
        gdf.to_postgis('hiking_trails', engine, if_exists='replace', index=False)
        print("Success!")
    else:
        print("No valid tracks found.")

if __name__ == "__main__":
    fetch_and_save_geometries()
