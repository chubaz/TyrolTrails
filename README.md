# 🏔️ TyrolTrails: 3D South Tyrol Trail Explorer

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)
![PostGIS](https://img.shields.io/badge/PostGIS-1E8C45?logo=postgresql&logoColor=white)
![Mapbox](https://img.shields.io/badge/Mapbox-000000?logo=mapbox&logoColor=white)

A high-performance 3D geospatial application for discovering hiking trails across the Dolomites and planning your journey with real-time alpine intelligence. Built using data from the **South Tyrol Open Data Hub (ODH)**.

---

## 🚀 Key Features

### 🗺️ 3D Alpine Engine
* **Immersive Terrain:** Full 3D terrain exploration with Mapbox GL JS, featuring 1.5x mountain exaggeration and atmospheric sky rendering.
* **Dynamic Trail Discovery:** Interactive map that automatically fetches and displays trails from the spatial database as you pan and zoom.
* **Precision Routing:** Powered by `pgRouting`, click *anywhere* on a trail line to snap to the nearest vertex and set custom start/end points.

### ⛰️ Integrated Alpine Services
* **Peak Explorer:** Automatically identifies and labels prominent mountain peaks in your 3D view using the OpenStreetMap Overpass API.
* **Live Summit Weather:** Real-time summit weather conditions (temperature and wind speed) fetched dynamically via the Open-Meteo API.
* **Live View:** Automatically retrieves open-source photographs of your destination peak via Wikimedia Commons.
* **Safety Warnings:** Calculates exact sunset times for your specific destination to ensure safe hiking planning.

### 🔄 Advanced Trail Intelligence
* **Circular Trail Handling:** Toggle between the "Direct Path" and the "Alternative Wrap-around" on any circular loop trail.
* **Dynamic Elevation Profile:** Interactive elevation chart sampling real-world altitude data along your custom-sliced route.
* **GPX Export:** Download your custom-calculated route as a standard GPX file for your Garmin or smartwatch.

### 🏨 Smart Accommodations & Gastronomy
* **Buffer Search:** Find hotels and pensions directly along your specific route section with a dynamic search radius slider.
* **Quick Actions:** Visual ratings and one-click "Call" or "Website" access directly from the map.

---

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, Uvicorn, SQLAlchemy
* **Database:** PostgreSQL + PostGIS + pgRouting (Spatial Analysis & Shortest Path calculations)
* **Data Processing:** GeoPandas, Pandas, Shapely
* **Frontend:** HTML5, CSS3, JavaScript, Mapbox GL JS v3, Turf.js, Chart.js
* **External APIs:** ODH South Tyrol, Overpass API, Open-Meteo, Wikimedia Commons, Sunrise-Sunset API

---

## 📖 How to Use the App

1. **Navigation & Search:** Use the sidebar search bar to fly instantly to any peak or town in South Tyrol. Hold `Right-Click` and drag to rotate the 3D camera.
2. **Plan Your Journey:** Zoom in and hover over a trail to highlight it. Click once to select it, then click two points on the line to set your **Start (Green)** and **End (Red)** points.
3. **Explore the Data:** The app will instantly generate the 3D route, drape it over the mountains, update the elevation chart, and fetch destination-specific weather, photos, and safety data.
4. **Find Facilities:** Adjust the Radius Slider to find accommodations near your route. Click a hotel card to fly the 3D camera directly to its location.

---

## 💻 Local Installation & Setup

### 1. Database Setup
Ensure you have PostgreSQL installed. You must enable the spatial extensions in your database before running the app:
```sql
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
```

### 2. Install Dependencies
Clone the repository and install the required Python packages:

```bash
git clone [https://github.com/YOUR_USERNAME/TyrolTrails.git](https://github.com/YOUR_USERNAME/TyrolTrails.git)
cd TyrolTrails
pip install -r requirements.txt
```
### 3. Environment Variables
Export your database connection URL (or update it directly in the Python scripts):

```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/hackathon_db"
```
### 4. Data Ingestion & Network Building
Run the data pipelines to fetch ODH data and build the pgRouting network topology:

```bash
python3 ingest_data.py
python3 build_network.py    # Crucial: Snaps geometries and builds routing nodes!
python3 ingest_pois.py      # Fetches accommodations
```
### 5. Frontend Configuration
Open index.html and replace the following placeholders at the top of the <script> block:

YOUR_MAPBOX_TOKEN: Your free Mapbox GL JS access token.

API_URL: Your backend API URL (e.g., http://127.0.0.1:8000).

### 6. Start the Server
Launch the FastAPI backend:

```bash
python3 app.py
```
Open index.html in your browser (or serve it via a local static server) and start exploring!

#### Built with ❤️ for the South Tyrol hiking community.
