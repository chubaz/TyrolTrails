import os
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import geopandas as gpd
from sqlalchemy import create_engine, text
import json
import pandas as pd
import numpy as np
from shapely import wkt
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Restrict allowed origins
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hackathon_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

try:
    with engine.connect() as conn:
        ELEV_EXISTS = conn.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_name='hiking_trails' AND column_name='elevation_up_m'")).scalar() > 0
except Exception: ELEV_EXISTS = False
ELEV_COL = "COALESCE(elevation_up_m, 0)" if ELEV_EXISTS else "0"

def get_nearest_vertex(lat: float, lon: float):
    """Finds the closest routing node that is actually used as a source or target in the noded trails."""
    sql = text("""
        SELECT 
            v.id as vertex_id,
            ST_X(v.geom) as lon,
            ST_Y(v.geom) as lat,
            ST_Distance(v.geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) as dist_to_node_m
        FROM hiking_trails_noded_vertices_pgr v
        WHERE v.id IN (SELECT source FROM hiking_trails_noded WHERE source IS NOT NULL UNION SELECT target FROM hiking_trails_noded WHERE target IS NOT NULL)
        ORDER BY v.geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        LIMIT 1;
    """)
    with engine.connect() as conn:
        res = conn.execute(sql, {"lat": lat, "lon": lon}).fetchone()
        if not res:
            return {"vertex_id": None, "lon": None, "lat": None, "distance_m": float('inf')}
        return {
            "vertex_id": res[0], 
            "lon": res[1], 
            "lat": res[2], 
            "distance_m": res[3]
        }

@app.get("/get-trails-in-view")
def get_trails_in_view(min_lat: float, min_lon: float, max_lat: float, max_lon: float):
    sql = text("SELECT id, name, geometry FROM hiking_trails WHERE geometry && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326) LIMIT 200")
    gdf = gpd.read_postgis(sql, engine, geom_col='geometry', params={"min_lon": min_lon, "min_lat": min_lat, "max_lon": max_lon, "max_lat": max_lat})
    return json.loads(gdf.to_json())

@app.get("/get-route")
def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float, trail_id: int, alt: bool = False):
    try:
        sql = text(f"""
            WITH raw_trail AS (SELECT ST_LineMerge(ST_Collect(geometry)) as geom, COALESCE(length_m, ST_Length(ST_Collect(geometry)::geography)) as length_m, {ELEV_COL} as elev FROM hiking_trails WHERE id = :tid GROUP BY length_m, elevation_up_m LIMIT 1),
                 points AS (
                    SELECT ST_LineLocatePoint(geom, ST_SetSRID(ST_MakePoint(:slon, :slat), 4326)) as f1,
                           ST_LineLocatePoint(geom, ST_SetSRID(ST_MakePoint(:elon, :elat), 4326)) as f2,
                           (ST_DistanceSphere(ST_StartPoint(geom), ST_EndPoint(geom)) < 20) as is_loop
                    FROM raw_trail
                 ),
                 sliced AS (
                    SELECT 
                        CASE 
                            WHEN NOT :alt THEN ST_LineSubstring(t.geom, LEAST(p.f1, p.f2), GREATEST(p.f1, p.f2))
                            ELSE ST_LineMerge(ST_Union(ST_LineSubstring(t.geom, GREATEST(p.f1, p.f2), 1.0), ST_LineSubstring(t.geom, 0.0, LEAST(p.f1, p.f2))))
                        END as geom,
                        CASE 
                            WHEN NOT :alt THEN (p.f1 > p.f2)
                            ELSE FALSE
                        END as should_reverse,
                        t.length_m, t.elev, p.is_loop 
                    FROM raw_trail t, points p
                 )
            SELECT 
                CASE WHEN should_reverse THEN ST_AsText(ST_Reverse(geom)) ELSE ST_AsText(geom) END,
                COALESCE(length_m * ST_Length(geom::geography) / NULLIF(ST_Length((SELECT geom FROM raw_trail)::geography), 0), ST_Length(geom::geography)) as sub_len, 
                elev, is_loop, length_m as total_len
            FROM sliced
        """)
        with engine.connect() as conn:
            res = conn.execute(sql, {"tid": trail_id, "slat": start_lat, "slon": start_lon, "elat": end_lat, "elon": end_lon, "alt": alt}).fetchone()
            if not res or not res[0]: return {"geojson": {"features": []}, "stats": {"actual_dist": 0}}
            wkt_geom, dist, elev, is_loop, total_len = res
            dist = float(dist or 0)
            total_len = float(total_len or 1) # Avoid division by zero
            gdf = gpd.GeoDataFrame([{"id": trail_id, "geometry": wkt.loads(wkt_geom)}], crs="EPSG:4326")
            
            # Calculate elevation proportionally for the sliced segment
            sub_elev = round(float(elev or 0) * (dist / total_len), 1)
            
            return {
                "geojson": json.loads(gdf.to_json()), 
                "is_loop": bool(is_loop), 
                "stats": {
                    "actual_dist": round(dist, 2), 
                    "perceived_dist": round(dist + (sub_elev * 10), 2), 
                    "elevation_gain": sub_elev, 
                    "est_duration_min": round((dist / 66.6) + (sub_elev / 10.0))
                }
            }
    except Exception as e:
        logger.error(f"Route error: {e}")
        return Response(content=str(e), status_code=500)

@app.get("/get-hotels")
def get_hotels(trail_id: int, start_lat: float, start_lon: float, end_lat: float, end_lon: float, radius: int = 2000, alt: bool = False):
    try:
        sql = text(f"""
            WITH trail AS (SELECT ST_LineMerge(ST_Collect(geometry)) as geom FROM hiking_trails WHERE id = :tid),
                 points AS (SELECT ST_LineLocatePoint(t.geom, ST_SetSRID(ST_MakePoint(:slon, :slat), 4326)) as f1, ST_LineLocatePoint(t.geom, ST_SetSRID(ST_MakePoint(:elon, :elat), 4326)) as f2 FROM trail t),
                 section AS (
                    SELECT CASE WHEN NOT :alt THEN ST_LineSubstring(t.geom, LEAST(p.f1, p.f2), GREATEST(p.f1, p.f2))
                           ELSE ST_LineMerge(ST_Union(ST_LineSubstring(t.geom, GREATEST(p.f1, p.f2), 1.0), ST_LineSubstring(t.geom, 0.0, LEAST(p.f1, p.f2)))) END as geom
                    FROM trail t, points p
                 )
            SELECT a.name, a.type, a.category, a.city, a.phone, a.website, a.latitude, a.longitude, a.image_url, a.street,
                   ROUND(ST_DistanceSphere((SELECT geom FROM section), a.geometry)::numeric, 0) as dist
            FROM accommodations a
            WHERE ST_DWithin(ST_Transform((SELECT geom FROM section), 3857), ST_Transform(a.geometry, 3857), :radius)
            ORDER BY dist ASC LIMIT 20;
        """)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"tid": trail_id, "slat": start_lat, "slon": start_lon, "elat": end_lat, "elon": end_lon, "alt": alt, "radius": radius})
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            return JSONResponse(content=df.to_dict(orient='records'))
    except Exception as e:
        logger.error(f"Hotels error: {e}")
        return JSONResponse(content=[])

@app.get("/get-stations")
def get_stations(trail_id: int, start_lat: float, start_lon: float, end_lat: float, end_lon: float, radius: int = 5000, alt: bool = False):
    try:
        sql = text("""
            WITH trail AS (SELECT ST_LineMerge(ST_Collect(geometry)) as geom FROM hiking_trails WHERE id = :tid),
                 points AS (SELECT ST_LineLocatePoint(t.geom, ST_SetSRID(ST_MakePoint(:slon, :slat), 4326)) as f1, ST_LineLocatePoint(t.geom, ST_SetSRID(ST_MakePoint(:elon, :elat), 4326)) as f2 FROM trail t),
                 section AS (
                    SELECT CASE WHEN NOT :alt THEN ST_LineSubstring(t.geom, LEAST(p.f1, p.f2), GREATEST(p.f1, p.f2))
                           ELSE ST_LineMerge(ST_Union(ST_LineSubstring(t.geom, GREATEST(p.f1, p.f2), 1.0), ST_LineSubstring(t.geom, 0.0, LEAST(p.f1, p.f2)))) END as geom
                    FROM trail t, points p
                 )
            SELECT m.name, m.temperature, m.latitude, m.longitude,
                   ROUND(ST_DistanceSphere((SELECT geom FROM section), m.geometry)::numeric, 0) as dist
            FROM measuring_points m
            WHERE ST_DWithin(ST_Transform((SELECT geom FROM section), 3857), ST_Transform(m.geometry, 3857), :radius)
            ORDER BY dist ASC LIMIT 10;
        """)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"tid": trail_id, "slat": start_lat, "slon": start_lon, "elat": end_lat, "elon": end_lon, "alt": alt, "radius": radius})
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            return JSONResponse(content=df.to_dict(orient='records'))
    except Exception as e:
        logger.error(f"Stations error: {e}")
        return JSONResponse(content=[])

@app.get("/get-nearest-node-on-trail")
def get_nearest_node_on_trail(lat: float, lon: float, trail_id: int):
    sql = text("SELECT ST_Y(p.g) as y, ST_X(p.g) as x FROM (SELECT ST_ClosestPoint(ST_LineMerge(ST_Collect(geometry)), ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) as g FROM hiking_trails WHERE id = :tid) p")
    with engine.connect() as conn:
        res = conn.execute(sql, {"lat": lat, "lon": lon, "tid": trail_id}).fetchone()
        return {"lat": res[0], "lon": res[1]} if res else {"error": "Not found"}

@app.get("/get-multi-trail-route")
def get_multi_trail_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    try:
        # 1. Snap Start and End points to the network
        start_node = get_nearest_vertex(start_lat, start_lon)
        end_node = get_nearest_vertex(end_lat, end_lon)
        
        logger.info(f"Snapped Start: {start_node['vertex_id']} (dist: {start_node['distance_m']:.2f}m)")
        logger.info(f"Snapped End: {end_node['vertex_id']} (dist: {end_node['distance_m']:.2f}m)")

        # 2. Check if the distance to the network is unreasonable (e.g., > 2km)
        if start_node['distance_m'] > 2000 or end_node['distance_m'] > 2000:
            return {"error": "Start or End point is too far from any hiking trail."}

        # 3. Run pgRouting between the snapped nodes
        sql = text(f"""
            WITH route AS (
                SELECT r.seq, t.geom as geometry, t.length_m, COALESCE(t.elevation_up_m, 0) as elev
                FROM pgr_dijkstra(
                    'SELECT id, source, target, (COALESCE(length_m, 0) + COALESCE(elevation_up_m, 0) * 10) AS cost FROM hiking_trails_noded WHERE source IS NOT NULL AND target IS NOT NULL',
                    :start_vid, 
                    :end_vid, 
                    false
                ) AS r
                JOIN hiking_trails_noded t ON r.edge = t.id
                ORDER BY r.seq
            )
            SELECT 
                ST_AsText(ST_LineMerge(ST_Collect(geometry))) as route_geom,
                SUM(length_m) as trail_dist,
                SUM(elev) as trail_elev
            FROM route;
        """)
        
        with engine.connect() as conn:
            res = conn.execute(sql, {"start_vid": start_node['vertex_id'], "end_vid": end_node['vertex_id']}).fetchone()
            
            if not res or not res[0]:
                return {"error": "No continuous path found between those trails."}
            
            wkt_geom, trail_dist, trail_elev = res
            
            # Combine the geometry so Leaflet can draw it
            gdf = gpd.GeoDataFrame([{"geometry": wkt.loads(wkt_geom)}], crs="EPSG:4326")
            
            # 4. Sum the total metrics
            total_dist = trail_dist + start_node['distance_m'] + end_node['distance_m']
            
            return {
                "geojson": json.loads(gdf.to_json()),
                "stats": {
                    "total_dist_m": round(total_dist, 2),
                    "off_trail_dist_m": round(start_node['distance_m'] + end_node['distance_m'], 2),
                    "elevation_gain_m": round(trail_elev, 2),
                    "est_duration_min": round((total_dist / 66.6) + (float(trail_elev or 0) / 10.0))
                }
            }
            
    except Exception as e:
        logger.error(f"Multi-trail route error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
