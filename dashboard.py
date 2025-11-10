import streamlit as st
import os
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
import time
from geopy.geocoders import Nominatim

# Load environment variables
load_dotenv(dotenv_path=os.path.join("backend", ".env"))

SUPABASE_URL = os.getenv("MY_SUPABASE_URL")
SERVICE_KEY = os.getenv("MY_SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SERVICE_KEY:
    st.error("Supabase URL or Service Role Key not set in .env")
    st.stop()

BASE_FUNCTION_URL = f"{SUPABASE_URL}/functions/v1/terrascope"
GET_DATA_URL = f"{BASE_FUNCTION_URL}/data"
POST_ADD_URL = f"{BASE_FUNCTION_URL}/add"

HEADERS = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json"
}

geolocator = Nominatim(user_agent="terrascope-dashboard")

def detect_location(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
        return location.address if location else "Unknown"
    except Exception:
        return "Unknown"

def classify_status(row):
    soil = row.get("soil_moisture", 0) or 0
    veg = row.get("vegetation", 0) or 0
    if soil >= 40 and veg >= 0.6:
        return "Healthy", "Maintain current practices"
    elif 20 <= soil < 40 or 0.4 <= veg < 0.6:
        return "At Risk", "Use cover crops or moderate irrigation"
    else:
        return "Degraded", "Reforestation or intensive irrigation"

st.set_page_config(page_title="Terrascope Dashboard", layout="wide")
st.title("🌿 Terrascope Land Health Dashboard")

@st.cache_data(ttl=60)
def fetch_data():
    start = time.time()
    try:
        res = requests.get(GET_DATA_URL, headers=HEADERS)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())

            if "vegetation_index" in df.columns:
                df.rename(columns={"vegetation_index": "vegetation"}, inplace=True)

            df["latitude"] = pd.to_numeric(df.get("latitude", 0), errors="coerce")
            df["longitude"] = pd.to_numeric(df.get("longitude", 0), errors="coerce")

            for col in ["soil_moisture", "vegetation", "temperature", "location", "beacon_id", "carbon_estimate", "sustainability_index"]:
                if col not in df.columns:
                    df[col] = None

            df["beacon_id"] = df["beacon_id"].fillna("BEACON-" + df.index.to_series().astype(str))
            df["sustainability_index"] = df["sustainability_index"].fillna(
                (0.5 * df["soil_moisture"].fillna(0) + 0.5 * df["vegetation"].fillna(0)).clip(lower=0, upper=100)
            )
            df["carbon_estimate"] = df["carbon_estimate"].fillna(df["vegetation"].fillna(0) * 1000)

            df[["status", "suggestion"]] = df.apply(classify_status, axis=1, result_type="expand")
            df["status"] = df["status"].astype(str).str.strip().str.title()

            df["detected_location"] = df.apply(
                lambda row: detect_location(row["latitude"], row["longitude"])
                if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"])
                else "Unknown",
                axis=1
            )

            df["processing_time"] = round(time.time() - start, 2)
            return df
        else:
            st.error(f"Failed to fetch data. Status code: {res.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = fetch_data()

# Sidebar
st.sidebar.title("⚙️ Dashboard Controls")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()


with st.sidebar.expander("📤 Upload CSV Data"):
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file:
        try:
            new_data = pd.read_csv(uploaded_file)
            st.success("File uploaded successfully.")
            st.dataframe(new_data.head())
        except Exception as e:
            st.error(f"Error reading file: {e}")

with st.sidebar.expander("🔍 Filter Data", expanded=True):
    all_statuses = sorted(df["status"].dropna().unique()) if "status" in df.columns else []
    status_filter = st.multiselect("Select Land Status:", options=all_statuses, default=all_statuses)
    filtered_df = df[df["status"].isin(status_filter)] if "status" in df.columns else df

with st.sidebar.expander("➕ Add New Land Data"):
    with st.form("add_form"):
        soil = st.number_input("Soil Moisture (%)", min_value=0.0, max_value=100.0, step=0.1)
        vegetation = st.number_input("Vegetation Index (NDVI)", min_value=0.0, max_value=1.0, step=0.01)
        temp = st.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, step=0.1)
        lat = st.number_input("Latitude", step=0.0001)
        lon = st.number_input("Longitude", step=0.0001)
        location = st.text_input("Location Name", "New Area")

        submitted = st.form_submit_button("Submit Data")
        if submitted:
            status, suggestion = classify_status({"soil_moisture": soil, "vegetation": vegetation})
            payload = {
                "location": location,
                "soil_moisture": soil,
                "vegetation_index": vegetation,
                "temperature": temp,
                "latitude": lat,
                "longitude": lon,
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "suggestion": suggestion
            }
            try:
                res = requests.post(POST_ADD_URL, headers=HEADERS, json=payload)
                if res.status_code in [200, 201]:
                    st.success("Data added successfully.")
                    st.cache_data.clear()
                    st.rerun()

                else:
                    st.error(f"Failed to upload data. Status code: {res.status_code}")
            except Exception as e:
                st.error(f"Error uploading data: {e}")
with st.sidebar.expander("📥 Download Data"):
    if not df.empty:
        csv_data = df.to_csv(index=False)
        st.download_button("Download Current Data as CSV", csv_data, "land_data.csv", "text/csv")
    else:
        st.info("No data to download.")

# Main Dashboard
if not df.empty:
    st.subheader("📊 Performance Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Records", len(df))
    col2.metric("% Healthy", f"{round(100 * len(df[df['status'] == 'Healthy']) / len(df), 1)}%")
    col3.metric("Avg Soil Moisture", f"{df['soil_moisture'].mean():.1f}%")
    col4.metric("Avg Vegetation", f"{df['vegetation'].mean():.2f}")
    col5.metric("Processing Time", f"{df['processing_time'].iloc[0]}s")

    st.subheader("📋 Land Data Table")
    st.dataframe(filtered_df, use_container_width=True)

    st.subheader("🗺️ Land Health Map")
    map_df = filtered_df.dropna(subset=["latitude", "longitude"])
    if not map_df.empty:
        fig = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="status",
            hover_name="detected_location",
            hover_data=[
                "location", "beacon_id", "soil_moisture", "vegetation", "temperature",
                "suggestion", "carbon_estimate", "sustainability_index"
            ],
            color_discrete_map={
                "Healthy": "#2E8B57",
                "At Risk": "#DAA520",
                "Degraded": "#8B0000"
            },
            zoom=4,
            height=600
        )
        fig.update_traces(marker=dict(size=12), text=map_df["beacon_id"], textposition="top center")
        fig.update_layout(
            mapbox_style="open-street-map",
            legend_title="Land Health Status",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Filtered data has no valid coordinates. Try adjusting the status filter.")
else:
    st.warning("No data available yet. Add or upload some to begin.")
