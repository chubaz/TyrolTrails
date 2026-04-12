# 🏔️ TyrolTrails: South Tyrol Trail Explorer

A professional-grade geospatial application for discovering hiking trails across the Dolomites and planning your journey with integrated accommodation discovery.

## 🚀 Key Features

*   **Dynamic Trail Discovery**: Interactive map that automatically fetches and displays trails as you pan and zoom.
*   **Precision Routing**: Click *anywhere* on a trail line to set your start and end points—not just at pre-defined corners.
*   **Circular Trail Intelligence**: 
    *   **Side Switching**: Toggle between the "Direct Path" and the "Alternative Wrap-around" on any circular loop.
    *   **Whole-Loop Detection**: Automatically recognizes and calculates the full journey if you start and end at the same point.
*   **Smart "Perceived" Metrics**: Calculates hiking time using Naismith's Rule, accounting for both horizontal distance and elevation gain.
*   **Integrated Accommodations**: 
    *   Find hotels, pensions, and farm stays directly along your specific route section.
    *   Visual ratings (Stars ⭐, Suns ☀️, Flowers 🌻).
    *   One-click "Call" and "Website" buttons for instant booking.
*   **GPX Export**: Download your custom-sliced route as a standard GPX file for use in handheld GPS devices or mobile apps.

---

## 🛠️ Tech Stack

*   **Backend**: FastAPI (Python)
*   **Database**: PostgreSQL + PostGIS + pgRouting
*   **Frontend**: Leaflet.js + Turf.js
*   **Data Source**: Open Data Hub (ODH) South Tyrol API

---

## 📖 How to Use the App

### 1. Discover a Trail
*   **Zoom in** to any area in South Tyrol. Trails will appear as faint grey "Ghost" lines.
*   **Hover** over a trail to see it highlight.
*   **Click a trail** to "Activate" it. All other trails will fade out so you can focus on your choice.

### 2. Plan Your Journey
*   **Set Start Point**: Click anywhere on the bold blue trail line to drop a **Green Marker**.
*   **Set End Point**: Click another spot on the same blue line to drop a **Red Marker**.
*   The app will instantly map the journey between those two points.

### 3. Handle Circular Loops
*   If the trail is a loop, a **"Switch Path Side"** button will appear in the sidebar.
*   Click it to instantly toggle between the two ways around the circle. The stats and hotel list will update automatically.

### 4. Explore Accommodations
*   Adjust the **Radius Slider** in the sidebar to search deeper into the landscape (up to 10km).
*   A blue "search zone" will appear around your path on the map.
*   **Click a Hotel Card** in the sidebar to zoom the map directly to that building.

### 5. Export
*   Once you are happy with your route, click **"Download GPX"** to save the file to your computer.

---

## 💻 Installation

1.  **Database Setup**: 
    Ensure you have PostgreSQL with the PostGIS and pgRouting extensions installed.
    ```sql
    CREATE EXTENSION postgis;
    CREATE EXTENSION pgrouting;
    ```

2.  **Ingest Data**:
    Run the ingestion scripts to fetch the latest trails and hotels from the Open Data Hub.
    ```bash
    python3 ingest_data.py
    python3 ingest_pois.py
    ```

3.  **Start the Server**:
    ```bash
    python3 app.py
    ```

4.  **View the Map**:
    Open `index.html` in any modern web browser.

---

*Built with ❤️ for the South Tyrol hiking community.*
