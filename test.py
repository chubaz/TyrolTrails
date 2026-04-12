import geopandas as gpd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:postgres@localhost:5432/hackathon_db')

def visual_audit():
    # Load 20 random trails
    sql = "SELECT name, geometry FROM hiking_trails ORDER BY RANDOM() LIMIT 20"
    gdf = gpd.read_postgis(sql, engine, geom_col='geometry')
    
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