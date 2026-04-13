# 🏔️ TyrolTrails: 3D South Tyrol Trail Explorer

A high-performance 3D geospatial application for discovering hiking trails across the Dolomites and planning your journey with real-time alpine intelligence.

## 🚀 Key Features

*   **3D Alpine Engine**: Full 3D terrain exploration with Mapbox GL JS, featuring 1.5x mountain exaggeration and atmospheric sky rendering.
*   **Dynamic Trail Discovery**: Interactive map that automatically fetches and displays trails from your database as you explore.
*   **Precision Routing**: Click *anywhere* on a trail line to set your start and end points—not just at pre-defined nodes.
*   **Integrated Alpine Services**:
    *   **Peak Explorer**: Automatically identifies prominent mountain peaks in your view using the Overpass API (Wikipedia-linked).
    *   **Live Weather**: Real-time summit weather conditions (temperature and wind) from the Open-Meteo API.
    *   **Live View**: Automatically fetches open-source photographs of your destination via Wikimedia Commons.
    *   **Safety Warning**: Calculates exact sunset times for your destination to ensure safe hiking planning.
*   **Circular Trail Intelligence**: 
    *   **Side Switching**: Toggle between the "Direct Path" and the "Alternative Wrap-around" on any circular loop.
*   **Elevation Profile**: Interactive elevation chart sampling real-world altitude data along your custom route.
*   **Integrated Accommodations**: 
    *   Find hotels and pensions directly along your specific route section with dynamic search radius.
    *   Visual ratings and one-click "Call" or "Website" access.
*   **GPX Export**: Download your custom-sliced route as a standard GPX file.

---

## 🛠️ Tech Stack

*   **Backend**: FastAPI (Python)
*   **Database**: PostgreSQL + PostGIS
*   **Frontend**: Mapbox GL JS v3, Turf.js, Chart.js
*   **Data Sources**: Open Data Hub (ODH) South Tyrol, Overpass API, Open-Meteo, Wikipedia/Wikimedia

---

## 📖 How to Use the App

### 1. Navigation & Search
*   **Search**: Use the sidebar search bar to fly instantly to any peak or town in South Tyrol.
*   **3D Camera**: Hold **Right-Click** and drag to rotate the camera. Use the scroll wheel to zoom and tilt.

### 2. Plan Your Journey
*   **Activate Trail**: Zoom in and hover over a trail to highlight it. Click once to select it.
*   **Set Points**: Click on the active trail to set your **Start** (Green) and **End** (Red) points.
*   The app will instantly generate the 3D route, update the elevation chart, and fetch destination-specific weather and photos.

### 3. Handle Loops & Hotels
*   For loop trails, use the **"Switch Path Side"** button to toggle direction.
*   Adjust the **Radius Slider** to find accommodations near your route. Click a hotel card to fly the 3D camera directly to its location.

---

## 💻 Installation

1.  **Database Setup**: 
    Ensure you have PostgreSQL with the PostGIS extension installed.
    ```sql
    CREATE EXTENSION postgis;
    ```

2.  **Ingest Data**:
    ```bash
    python3 ingest_data.py
    python3 ingest_pois.py
    ```

3.  **Configuration**:
    Open `index.html` and replace the following placeholders:
    *   `YOUR_MAPBOX_TOKEN`: Your Mapbox GL JS access token.
    *   `YOUR_API_BASE_URL`: Your backend API URL (e.g., `http://localhost:8000` or an ngrok URL).

4.  **Start the Server**:
    ```bash
    python3 app.py
    ```

---

*Built with ❤️ for the South Tyrol hiking community.*
