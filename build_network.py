from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@localhost:5432/hackathon_db')

def build_routing_topology():
    print("Preparing the network graph for routing...")
    
    # We use AUTOCOMMIT so PostgreSQL lets us create extensions and ignore minor column errors
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        
        # 1. Force activate pgRouting just in case!
        print("1. Activating pgRouting extension...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgrouting;"))
        except Exception as e:
            print(f"Warning/Error creating extension: {e}")

        # 2. Add the columns pgRouting needs
        print("2. Adding routing columns...")
        try:
            conn.execute(text("ALTER TABLE hiking_trails ADD COLUMN id SERIAL PRIMARY KEY;"))
        except Exception: 
            pass # Ignores error if column already exists
        try:
            conn.execute(text("ALTER TABLE hiking_trails ADD COLUMN source integer;"))
        except Exception: 
            pass
        try:
            conn.execute(text("ALTER TABLE hiking_trails ADD COLUMN target integer;"))
        except Exception: 
            pass

        # 3. Snap geometries (Replacing the tolerance argument from the old function)
        print("3. Snapping trail geometries to grid (tolerance: 0.00001)...")
        conn.execute(text("""
            UPDATE hiking_trails 
            SET geometry = ST_SnapToGrid(geometry, 0.00001);
        """))

        # 4. Build the Topology using pgRouting 4.0+ functions
        print("4. Extracting vertices and building topology. This might take a minute...")
        
        # A. Create the vertices table
        conn.execute(text("""
            DROP TABLE IF EXISTS hiking_trails_vertices_pgr;
            SELECT * INTO hiking_trails_vertices_pgr 
            FROM pgr_extractVertices('SELECT id, geometry AS geom FROM hiking_trails ORDER BY id');
        """))
        
        # B. Index the vertices for performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_hiking_vertices_geom 
            ON hiking_trails_vertices_pgr USING GIST (geom);
        """))

        # C. Update the source column
        conn.execute(text("""
            UPDATE hiking_trails AS e 
            SET source = v.id 
            FROM hiking_trails_vertices_pgr AS v 
            WHERE ST_StartPoint(e.geometry) = v.geom;
        """))

        # D. Update the target column
        conn.execute(text("""
            UPDATE hiking_trails AS e 
            SET target = v.id 
            FROM hiking_trails_vertices_pgr AS v 
            WHERE ST_EndPoint(e.geometry) = v.geom;
        """))

        print("Success! Network topology created for pgRouting 4.0+.")

if __name__ == "__main__":
    build_routing_topology()