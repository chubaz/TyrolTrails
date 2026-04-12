import geopandas as gpd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:postgres@localhost:5432/hackathon_db')

def export_shortest_path():
    print("Calculating route and exporting to GeoJSON...")
    
    # Replace these with the node IDs you just successfully tested!
    start_node = 14
    end_node = 13
    
    sql = f"""
    SELECT 
        r.seq, 
        t.name AS trail_name,
        t.geometry
    FROM 
        pgr_dijkstra(
            'SELECT id, source, target, length_m AS cost FROM hiking_trails',
            {start_node}, 
            {end_node}, 
            directed := false
        ) AS r
    JOIN 
        hiking_trails t ON r.edge = t.id
    ORDER BY 
        r.seq;
    """
    
    try:
        # GeoPandas can read the SQL query directly and parse those ugly hex strings!
        gdf = gpd.read_postgis(sql, engine, geom_col='geometry')
        
        if gdf.empty:
            print("No path found between those nodes.")
            return
            
        # Export for Leaflet
        gdf.to_file("shortest_path.geojson", driver="GeoJSON")
        print(f"Success! Exported {len(gdf)} trail segments to 'shortest_path.geojson'.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    export_shortest_path()