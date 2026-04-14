import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to PostGIS
engine = create_engine(DATABASE_URL)

def enrich_trail_with_pois(track_id, distance_meters=2000):
    print(f"Drawing a {distance_meters}m buffer around trail: {track_id}...")
    
    # Use parameterized query and ST_DistanceSphere
    sql = text("""
    SELECT 
        t.name AS trail_name,
        a.name AS hotel_name,
        a.type AS hotel_type,
        ROUND(ST_DistanceSphere(t.geometry, a.geometry)::numeric, 0) AS distance_m,
        a.latitude,
        a.longitude
    FROM 
        hiking_trails t
    JOIN 
        accommodations a 
    ON 
        ST_DWithin(ST_Transform(t.geometry, 3857), ST_Transform(a.geometry, 3857), :dist)
    WHERE 
        t.track_id = :tid
    ORDER BY 
        distance_m ASC;
    """)
    
    # Execute the query and load results into a Pandas DataFrame
    try:
        with engine.connect() as conn:
            nearby_pois = pd.read_sql(sql, conn, params={"tid": track_id, "dist": distance_meters})
        
        if nearby_pois.empty:
            print("No accommodations found within that distance.")
            return
            
        print(f"\nSuccess! Found {len(nearby_pois)} nearby accommodations.")
        print("-" * 40)
        
        # Print the top 5 closest hotels to the terminal so you can see it working
        print(nearby_pois[['hotel_name', 'distance_m']].head())
        
        # Save to a JSON file for your Leaflet frontend!
        output_filename = f"nearby_hotels.json"
        nearby_pois.to_json(output_filename, orient='records', indent=2)
        print(f"\nSaved results to {output_filename} for mapping.")
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    # Let's test it on the first trail we downloaded, looking within a 5km radius (5000m)
    enrich_trail_with_pois('routes-hikingtrails.11426062', 5000)