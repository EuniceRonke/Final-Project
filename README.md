🌍 TerraScope: Land Health Monitoring Dashboard
TerraScope is a real-time, interactive dashboard that helps visualize and monitor land health across Africa using satellite-derived environmental data. 
Built with Streamlit, Supabase, and Plotly, it empowers researchers, farmers, and policymakers to make data-driven decisions for sustainable land management.


✨ Why I Built TerraScope
Land degradation is a growing challenge in many parts of Africa. I created TerraScope to:
- Visualize land health using real environmental data
- Make it easy to track changes in soil moisture, vegetation, and temperature
- Provide actionable insights through classification and suggestions
- Learn how to build full-stack data apps using modern tools


🚀 Features
- 🗺️ Interactive Map: View land health status across regions using Plotly Mapbox
- 📊 Performance Metrics: Real-time summaries of soil moisture, vegetation, and temperature
- 📥 CSV Upload: Add multiple land records at once
- ➕ Manual Entry: Add new land data via form input
- 🔍 Filter by Status: View only Healthy, At Risk, or Degraded lands
- 📤 Download Data: Export current dataset as CSV
- 🔄 Live Updates: New entries appear instantly on the map after submission

🧠 How It Works
- Data Source: Land data is stored in a Supabase Postgres database and accessed via Supabase Edge Functions.
- Classification Logic:
- Healthy: Soil Moisture ≥ 40% and Vegetation Index ≥ 0.6
- At Risk: Soil Moisture 20–39% or Vegetation Index 0.4–0.59
- Degraded: Soil Moisture < 20% or Vegetation Index < 0.4
- Location Detection: Reverse geocoding using Nominatim (OpenStreetMap)
- Sustainability Index: Weighted average of soil moisture and vegetation
- Carbon Estimate: Approximated as vegetation × 1000

🗺️ TerraScope Map Overview
The map is built using Plotly Mapbox, which allows for interactive, high-resolution geospatial visualization. Each land record is plotted as a colored marker based on its health status.
 Legend: Color-Coded Land Status
Each marker represents a land entry and is color-coded according to its classification:
| Status   | Color   | Criteria  
| Healthy  | Green   | Soil Moisture ≥ 40% and Vegetation ≥ 0.6  
|At Risk   | Orange  | Soil Moisture 20–39% or Vegetation 0.4–0.59  
| Degraded | Red     | Soil Moisture < 20% or Vegetation < 0.4  
This legend helps users instantly identify which areas need attention.

🔍 Zooming & Navigation
- Zoom In/Out: Use your mouse scroll wheel or pinch on touch devices.
- Pan: Click and drag to move across the map.
- Reset View: Double-click anywhere to reset the zoom.
- Hover Tooltips: Hover over a marker to see detailed info:
- Location name
- Soil moisture
- Vegetation index
- Temperature
- Sustainability index
- Carbon estimate

🧭 Filtering by Status
Users can filter the map to show only:
- Healthy lands
- At Risk lands
- Degraded lands
This makes it easier to focus on specific regions or prioritize interventions.

📍 Location Detection
Each marker is enriched with reverse geocoded location names using Nominatim, so users see familiar place names instead of raw coordinates.

🌱 Sustainability & Carbon Intelligence in TerraScope
♻️ Sustainability Index
TerraScope calculates a Sustainability Index for each land record to reflect its ecological health. This index is a weighted average of:
- Soil Moisture (weight: 0.6)
- Vegetation Index (weight: 0.4)
This gives a quick snapshot of how resilient or vulnerable a land area is to degradation.
sustainability_index = (soil_moisture * 0.6) + (vegetation * 0.4)

🌍 Carbon Estimate
To support climate-conscious decision-making, TerraScope estimates carbon sequestration potential using:
carbon_estimate = vegetation * 1000  # in kg CO₂ equivalent
This is a simplified model that helps users compare regions and prioritize restoration efforts.

⚡ Processing Time & Green Efficiency
TerraScope is designed to be lightweight and fast:
- ✅ Uses cached data to reduce redundant API calls
- ✅ Loads only essential libraries (Streamlit, Plotly, Pandas)
- ✅ Minimizes backend load by using Supabase Edge Functions
- ✅ Avoids heavy computation on the frontend
This makes it suitable for low-power devices and field deployment — a step toward sustainable tech.


🛠️ Tech Stack
|Layer  | Technology 
| Frontend | Streamlit 
| Backend | Supabase Edge Functions (Python) 
| Database | Supabase Postgres 
| Geolocation | Nominatim (OpenStreetMap) 
|Visualization  | Plotly + Mapbox 

📦 Installation
git clone https://github.com/EuniceRonke/Final-Project
cd terrascope-dashboard
pip install -r requirements.txt

🧪 Running Locally
streamlit run dashboard.py

🌍 Deployment
Streamlit Cloud:
Website: https://terrascope.streamlit.app/


🧪 Sample Data for Testing
| Location         | Soil Moisture | Vegetation | Temp   | Latitude | Longitude | Status | 
| Tillabéri, Niger | 42.8          |0.68        | 30.2   | 13.5128  | 2.1126    |Healthy  | 
| Sikasso, Mali    |45.2           | 0.72       | 28.5   |12.6392   |-8.0029    |Healthy  | 


🧠 Future Improvements
- 📡 IoT Integration: Connect real-time sensors to automatically stream soil moisture, temperature, and vegetation data into the dashboard.
- 🛰️ Satellite Sync: Integrate with remote sensing APIs (e.g., Copernicus, NASA Earthdata) for automated updates and broader coverage.
- 📈 Time-Series Tracking: Visualize changes in land health over time to monitor trends and impact of interventions.
- 📱 Mobile Optimization: Build a responsive version or companion app for field use by farmers and researchers.
- 🔔 Alert System: Notify users when land status shifts from Healthy to At Risk or Degraded.
- 🧾 Audit Trail: Track who added or modified data for better transparency and collaboration.
- 🧪 Experimental Modules: Add sandboxed tools for testing new sustainability metrics or carbon models.

📄 License
MIT License © 2025 Eunice
