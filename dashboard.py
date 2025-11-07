import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client
from datetime import datetime
from geopy.geocoders import Nominatim
import io

# --------------------------
# Supabase Setup
# --------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Page Setup
# --------------------------
st.set_page_config(page_title="TerraScope - Land Health Monitor", layout="wide")
st.title("🌍 TerraScope - Land Health Monitoring Dashboard")

# --------------------------
# Helper Functions
# --------------------------
def classify_status(soil_moisture, vegetation_index):
    if soil_moisture < 20 or vegetation_index < 0.3:
        return "Degraded", "Reforestation or irrigation needed."
    elif 20 <= soil_moisture < 35 or 0.3 <= vegetation_index < 0.5:
        return "At Risk", "Mulching, cover crops, or moderate irrigation."
    else:
        return "Healthy", "Land is healthy. Maintain current practices."

def get_color(status):
    return {"Healthy": "green", "At Risk": "orange", "Degraded": "red"}.get(status, "gray")

def get_location_name(lat, lon):
    try:
        geolocator = Nominatim(user_agent="terrascope")
        location = geolocator.reverse((lat, lon), timeout=10)
        return location.address if location else "Unknown Location"
    except Exception:
        return "Unknown Location"

# --------------------------
# Fetch Data
# --------------------------
try:
    response = supabase.table("land_data").select("*").execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Failed to fetch data: {e}")
    df = pd.DataFrame()

# --------------------------
# Clean and Process Data
# --------------------------
if not df.empty:
    df.drop_duplicates(subset=["latitude", "longitude", "soil_moisture", "vegetation_index"], inplace=True)
    df["status"], df["suggestion"] = zip(*df.apply(
        lambda row: classify_status(row["soil_moisture"], row["vegetation_index"]), axis=1
    ))

# --------------------------
# Sidebar - Filter and Add Data
# --------------------------
st.sidebar.header("Filter & Add Data")

status_filter = st.sidebar.selectbox("Filter by Status", ["All", "Healthy", "At Risk", "Degraded"])

with st.sidebar.form("add_data_form", clear_on_submit=True):
    st.write("Add New Land Data")
    soil_moisture = st.number_input("Soil Moisture (%)", min_value=0.0, max_value=100.0, step=0.1)
    vegetation_index = st.number_input("Vegetation Index (0–1)", min_value=0.0, max_value=1.0, step=0.01)
    temperature = st.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, step=0.1)
    latitude = st.number_input("Latitude", format="%.6f")
    longitude = st.number_input("Longitude", format="%.6f")

    if latitude != 0 and longitude != 0:
        detected_location = get_location_name(latitude, longitude)
        st.info(f"Detected Location: {detected_location}")
    else:
        detected_location = "Unknown Location"

    submit = st.form_submit_button("Submit Data")

    if submit:
        status, suggestion = classify_status(soil_moisture, vegetation_index)
        record = {
            "location": detected_location,
            "soil_moisture": soil_moisture,
            "vegetation_index": vegetation_index,
            "temperature": temperature,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "suggestion": suggestion,
        }
        try:
            supabase.table("land_data").insert(record).execute()
            st.success(f"✅ Data added for {detected_location} ({status})")
        except Exception as e:
            st.error(f"Error adding data: {e}")

# --------------------------
# Filter Data
# --------------------------
if not df.empty:
    if status_filter != "All":
        df = df[df["status"] == status_filter]

# --------------------------
# Map Visualization
# --------------------------
if not df.empty:
    m = folium.Map(location=[9.0820, 8.6753], zoom_start=5, tiles="OpenStreetMap")

    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=9,
            color=get_color(row["status"]),
            fill=True,
            fill_color=get_color(row["status"]),
            fill_opacity=0.9,
            popup=folium.Popup(
                f"<b>Location:</b> {row['location']}<br>"
                f"<b>Status:</b> {row['status']}<br>"
                f"<b>Soil Moisture:</b> {row['soil_moisture']}%<br>"
                f"<b>Vegetation Index:</b> {row['vegetation_index']}<br>"
                f"<b>Temperature:</b> {row['temperature']}°C<br>"
                f"<b>Suggestion:</b> {row['suggestion']}",
                max_width=300,
            ),
        ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; width: 160px;
                background-color: white; border:2px solid grey; border-radius:8px;
                padding: 10px; font-size:14px; z-index:9999;">
        <b>Legend:</b><br>
        <i style="background:green;width:12px;height:12px;border-radius:50%;display:inline-block;"></i> Healthy<br>
        <i style="background:orange;width:12px;height:12px;border-radius:50%;display:inline-block;"></i> At Risk<br>
        <i style="background:red;width:12px;height:12px;border-radius:50%;display:inline-block;"></i> Degraded
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st.subheader("🗺️ Land Health Map")
    st_folium(m, width=900, height=500)

    # --------------------------
    # Data Table & Download
    # --------------------------
    st.subheader("📋 Land Data Table")
    st.dataframe(df[["location", "latitude", "longitude", "soil_moisture",
                     "vegetation_index", "temperature", "status", "suggestion", "timestamp"]])

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Data as CSV",
        csv,
        "terrascope_land_data.csv",
        "text/csv",
        key='download-csv'
    )

    # --------------------------
    # File Upload Option
    # --------------------------
    st.subheader("📤 Upload Land Data CSV")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        new_data = pd.read_csv(uploaded_file)
        try:
            for _, row in new_data.iterrows():
                status, suggestion = classify_status(row["soil_moisture"], row["vegetation_index"])
                record = {
                    "location": row.get("location", "Uploaded Data"),
                    "soil_moisture": row["soil_moisture"],
                    "vegetation_index": row["vegetation_index"],
                    "temperature": row["temperature"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": status,
                    "suggestion": suggestion,
                }
                supabase.table("land_data").insert(record).execute()
            st.success("✅ Uploaded data successfully added!")
        except Exception as e:
            st.error(f"Error uploading data: {e}")

else:
    st.warning("No data available yet.")
