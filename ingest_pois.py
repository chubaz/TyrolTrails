import requests
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine

# Database connection with pooling
engine = create_engine(
    'postgresql://postgres:postgres@localhost:5432/hackathon_db',
    pool_pre_ping=True
)

def fetch_and_save_accommodations():
    poi_list = []
    page = 1
    
    print("1. Fetching ALL accommodations from API...")
    while True:
        api_url = f"https://tourism.api.opendatahub.com/v1/Accommodation?pagenumber={page}&pagesize=1000"
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
                    poi_id = item.get('Id')
                    details = item.get('AccoDetail', {})
                    detail = details.get('en') or details.get('de') or details.get('it') or {}
                    
                    latitude = item.get('Latitude')
                    longitude = item.get('Longitude')
                    
                    if latitude and longitude:
                        poi_list.append({
                            'poi_id': poi_id,
                            'name': detail.get('Name') or f"Accommodation {poi_id}",
                            'type': (item.get('AccoType') or {}).get('Id'),
                            'category': (item.get('AccoCategory') or {}).get('Id'),
                            'street': detail.get('Street'),
                            'zip': detail.get('Zip'),
                            'city': detail.get('City'),
                            'phone': detail.get('Phone'),
                            'email': detail.get('Email'),
                            'website': detail.get('Website'),
                            'description': detail.get('Longdesc') or detail.get('Shortdesc'),
                            'image_url': (item.get('ImageGallery', [{}])[0]).get('ImageUrl'),
                            'latitude': latitude,
                            'longitude': longitude
                        })
                except Exception:
                    continue
            
            print(f"   Fetched page {page} ({len(poi_list)} items total)...")
            page += 1
        except Exception as e:
            print(f"   Error fetching page {page}: {e}")
            break
            
    if not poi_list:
        print("No valid accommodations found.")
        return

    # Deduplication
    df = pd.DataFrame(poi_list)
    df = df.drop_duplicates(subset=['poi_id'])
    
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    )
    
    print(f"2. Saving {len(gdf)} unique accommodation records to PostGIS...")
    gdf.to_postgis('accommodations', engine, if_exists='replace', index=False)
    print("Success!")

if __name__ == "__main__":
    fetch_and_save_accommodations()
