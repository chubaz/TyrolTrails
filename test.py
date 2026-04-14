import os
from dotenv import load_dotenv
import geopandas as gpd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def visual_audit():
    # Load 20 random trails
    sql = text("SELECT name, geometry FROM hiking_trails ORDER BY RANDOM() LIMIT 20")
    with engine.connect() as conn:
        gdf = gpd.read_postgis(sql, conn, geom_col='geometry')
    
    if gdf.empty:
        print("Database is empty!")
        return

    print(f"Auditing {len(gdf)} trails...")
    print(gdf[['name']].head()) # Show names in terminal

    # Plot them
    gdf.plot(column='name', cmap='tab20', figsize=(10, 10))
    plt.title("Visual Audit: Sample Trails from PostGIS")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

if __name__ == "__main__":
    visual_audit()