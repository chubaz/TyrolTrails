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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

engine = create_engine('postgresql://postgres:postgres@localhost:5432/hackathon_db', pool_pre_ping=True)

try:
    with engine.connect() as conn:
        ELEV_EXISTS = conn.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_name='hiking_trails' AND column_name='elevation_up_m'")).scalar() > 0
except Exception: ELEV_EXISTS = False
ELEV_COL = "COALESCE(elevation_up_m, 0)" if ELEV_EXISTS else "0"

@app.get("/get-trails-in-view")
def get_trails_in_view(min_lat: float, min_lon: float, max_lat: float, max_lon: float):
    sql = text("SELECT id, name, geometry FROM hiking_trails WHERE geometry && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326) LIMIT 200")
    gdf = gpd.read_postgis(sql, engine, geom_col='geometry', params={"min_lon": min_lon, "min_lat": min_lat, "max_lon": max_lon, "max_lat": max_lat})
    return json.loads(gdf.to_json())

@app.get("/get-route")
def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float, trail_id: int, alt: bool = False):
    try:
        sql = text(f"""
            WITH raw_trail AS (SELECT ST_LineMerge(ST_Collect(geometry)) as geom, length_m, {ELEV_COL} as elev FROM hiking_trails WHERE id = :tid GROUP BY length_m, elevation_up_m LIMIT 1),
                 points AS (
                    SELECT ST_LineLocatePoint(geom, ST_SetSRID(ST_MakePoint(:slon, :slat), 4326)) as f1,
                           ST_LineLocatePoint(geom, ST_SetSRID(ST_MakePoint(:elon, :elat), 4326)) as f2,
                           (ST_Distance(ST_StartPoint(geom)::geography, ST_EndPoint(geom)::geography) < 20) as is_loop
                    FROM raw_trail
                 ),
                 sliced AS (
                    SELECT CASE WHEN NOT :alt THEN ST_LineSubstring(t.geom, LEAST(p.f1, p.f2), GREATEST(p.f1, p.f2))
                           ELSE ST_LineMerge(ST_Union(ST_LineSubstring(t.geom, GREATEST(p.f1, p.f2), 1.0), ST_LineSubstring(t.geom, 0.0, LEAST(p.f1, p.f2)))) END as geom,
                           t.length_m, t.elev, p.is_loop FROM raw_trail t, points p
                 )
            SELECT ST_AsText(geom), length_m * ST_Length(geom::geography) / NULLIF(ST_Length((SELECT geom FROM raw_trail)::geography), 0) as sub_len, elev, is_loop FROM sliced
        """)
        with engine.connect() as conn:
            res = conn.execute(sql, {"tid": trail_id, "slat": start_lat, "slon": start_lon, "elat": end_lat, "elon": end_lon, "alt": alt}).fetchone()
            if not res or not res[0]: return {"geojson": {"features": []}, "stats": {"actual_dist": 0}}
            wkt_geom, dist, elev, is_loop = res
            gdf = gpd.GeoDataFrame([{"id": trail_id, "geometry": wkt.loads(wkt_geom)}], crs="EPSG:4326")
            sub_elev = round(float(elev or 0) * (dist / 1000 if dist > 0 else 1), 1)
            return {"geojson": json.loads(gdf.to_json()), "is_loop": bool(is_loop), "stats": {"actual_dist": round(dist, 2), "perceived_dist": round(dist + (sub_elev * 10), 2), "elevation_gain": sub_elev, "est_duration_min": round((dist / 66.6) + (sub_elev / 10.0))}}
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
                   ROUND(ST_Distance((SELECT geom FROM section)::geography, a.geometry::geography)::numeric, 0) as dist
            FROM accommodations a
            WHERE ST_DWithin((SELECT geom FROM section)::geography, a.geometry::geography, :radius)
            ORDER BY dist ASC LIMIT 20;
        """)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"tid": trail_id, "slat": start_lat, "slon": start_lon, "elat": end_lat, "elon": end_lon, "alt": alt, "radius": radius})
            df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
            return JSONResponse(content=df.to_dict(orient='records'))
    except Exception as e:
        logger.error(f"Hotels error: {e}")
        return JSONResponse(content=[])

@app.get("/get-nearest-node-on-trail")
def get_nearest_node_on_trail(lat: float, lon: float, trail_id: int):
    sql = text("SELECT ST_Y(p.g) as y, ST_X(p.g) as x FROM (SELECT ST_ClosestPoint(ST_LineMerge(ST_Collect(geometry)), ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) as g FROM hiking_trails WHERE id = :tid) p")
    with engine.connect() as conn:
        res = conn.execute(sql, {"lat": lat, "lon": lon, "tid": trail_id}).fetchone()
        return {"lat": res[0], "lon": res[1]} if res else {"error": "Not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
