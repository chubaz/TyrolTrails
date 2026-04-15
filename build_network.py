import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or 'postgresql://postgres:postgres@localhost:5432/hackathon_db'
engine = create_engine(DATABASE_URL)

def build_routing_topology():
    print("\n🚀 Starting Hyper-Optimized Regional Network Repair...")
    
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        
        # 1. Start Fresh
        print("\n[1/5] Cleaning up previous attempts...")
        conn.execute(text("DROP TABLE IF EXISTS hiking_trails_noded CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS hiking_trails_noded_vertices_pgr CASCADE;"))
        
        # 2. Data Cleaning & Pre-calculating lengths (Eliminates the UPDATE step!)
        print("\n[2/5] Exploding MultiLineStrings and pre-calculating lengths...")
        conn.execute(text("""
            CREATE TABLE hiking_trails_noded AS
            WITH dumped_trails AS (
                SELECT id as old_id, name, elevation_up_m, (ST_Dump(ST_MakeValid(geometry))).geom as geom
                FROM hiking_trails
            )
            SELECT 
                old_id, 
                name, 
                elevation_up_m, 
                ST_SnapToGrid(geom, 0.00001) as geom,
                -- Compute length immediately instead of updating later!
                ST_Length(ST_SnapToGrid(geom, 0.00001)::geography) as length_m 
            FROM dumped_trails
            WHERE ST_GeometryType(geom) = 'ST_LineString';
            
            ALTER TABLE hiking_trails_noded ADD COLUMN id SERIAL PRIMARY KEY;
            ALTER TABLE hiking_trails_noded ADD COLUMN source integer;
            ALTER TABLE hiking_trails_noded ADD COLUMN target integer;
            
            -- HUGE SPEED BOOST: Index the geometry immediately
            CREATE INDEX idx_hiking_noded_geom ON hiking_trails_noded USING GIST (geom);
        """))

        # 3. THE BRIDGE BUILDER (Indexed Temporary Table)
        print("\n[3/5] Bridge Builder: Healing gaps between trail systems (Indexed)...")
        conn.execute(text("""
            -- Materialize endpoints into a temp table so we can index them
            CREATE TEMP TABLE trail_endpoints AS
            SELECT ST_StartPoint(geom) as pt, id FROM hiking_trails_noded
            UNION
            SELECT ST_EndPoint(geom) as pt, id FROM hiking_trails_noded;

            -- This index stops the O(N^2) cross-join!
            CREATE INDEX idx_endpoints_geom ON trail_endpoints USING GIST (pt);

            INSERT INTO hiking_trails_noded (geom, name, length_m)
            WITH bridges AS (
                SELECT DISTINCT ON (e1.pt)
                    ST_MakeLine(e1.pt, e2.pt) as bridge_geom
                FROM trail_endpoints e1
                JOIN trail_endpoints e2 ON e1.id != e2.id
                WHERE ST_DWithin(e1.pt, e2.pt, 0.001) 
                  AND ST_Distance(e1.pt, e2.pt) > 0.00001 
                ORDER BY e1.pt, ST_Distance(e1.pt, e2.pt)
            )
            SELECT 
                ST_SnapToGrid(bridge_geom, 0.00001), 
                'Virtual Connection',
                -- Pre-calculate bridge lengths
                ST_Length(ST_SnapToGrid(bridge_geom, 0.00001)::geography)
            FROM bridges;
            
            DROP TABLE trail_endpoints;
        """))

        # (Old Step 4 UPDATE is completely removed)

        # 4. Build Topology 
        print("\n[4/5] Building routing topology (linking nodes to vertices)...")
        try:
            conn.execute(text("""
                DROP TABLE IF EXISTS hiking_trails_noded_vertices_pgr;
                SELECT * INTO hiking_trails_noded_vertices_pgr 
                FROM pgr_extractVertices('SELECT id, geom FROM hiking_trails_noded ORDER BY id');
                
                CREATE INDEX idx_hiking_noded_vertices_geom 
                ON hiking_trails_noded_vertices_pgr USING GIST (geom);

                -- HUGE SPEED BOOST: Index the start and end points of the main table
                CREATE INDEX idx_start_pt ON hiking_trails_noded USING GIST(ST_StartPoint(geom));
                CREATE INDEX idx_end_pt ON hiking_trails_noded USING GIST(ST_EndPoint(geom));

                -- The indices above make these two UPDATEs lightning-fast
                UPDATE hiking_trails_noded AS e 
                SET source = v.id 
                FROM hiking_trails_noded_vertices_pgr AS v 
                WHERE ST_StartPoint(e.geom) = v.geom;

                UPDATE hiking_trails_noded AS e 
                SET target = v.id 
                FROM hiking_trails_noded_vertices_pgr AS v 
                WHERE ST_EndPoint(e.geom) = v.geom;
            """))
            print("      - Topology successfully created!")
        except Exception as e:
            print(f"      - Topology Error: {e}")

        # 5. Connectivity Analysis
        print("\n[5/5] Analyzing final connectivity (Island Analysis)...")
        try:
            sql_islands = text("""
                SELECT count(DISTINCT component) 
                FROM pgr_connectedComponents(
                    'SELECT id, source, target, COALESCE(length_m, 1) as cost FROM hiking_trails_noded WHERE source IS NOT NULL AND target IS NOT NULL'
                );
            """)
            island_count = conn.execute(sql_islands).scalar()
            print(f"\n✅ SUCCESS! Regional network now has {island_count} connected components.")
        except Exception as e:
            print(f"      - Connectivity check failed: {e}")

if __name__ == "__main__":
    build_routing_topology()