import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
from geopy.geocoders import Nominatim

# --- Page setup ---
st.set_page_config(page_title="Terrascope Dashboard", layout="wide")

# --- Connect to Supabase ---
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

st.title("🌍 Terrascope Land Health Dashboard")

# --- Classification and suggestion logic ---
def classify_status(row):
    try:
        if row["soil_moisture"] >= 35 and row["vegetation_index"] >= 0.6:
            return "Healthy"
        elif 20 <= row["soil_moisture"] < 35 or 0.4 <= row["vegetation_index"] < 0.6:
            return "At Risk"
        elif row["soil_moisture"] < 20 or row["vegetation_index"] < 0.4:
            return "Degraded"
        else:
            return "Critical"
    except Exception:
        return "Unknown"

def generate_suggestion(status):
    suggestions = {
        "Healthy": "Land is healthy. Maintain current practices.",
        "At Risk": "Monitor soil conditions. Mild intervention may help.",
        "Degraded": "Reforestation or irrigation is recommended.",
        "Critical": "Immediate restoration needed — consider intensive soil recovery.",
        "Unknown": "No suggestion available.",
    }
    return suggestions.get(status, "No suggestion available.")

# --- Load data from Supabase ---
@st.cache_data
def load_data():
    response = supabase.table("land_data").select("*").execute()
    return pd.DataFrame(response.data)

df = load_data()

# --- Clean data and auto-classify missing records ---
if not df.empty:
    df.columns = df.columns.str.lower()
    for col in ["soil_moisture", "vegetation_index", "temperature"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "status" not in df.columns:
        df["status"] = None
    if "suggestion" not in df.columns:
        df["suggestion"] = None

    df["status"] = df.apply(lambda x: classify_status(x) if pd.isna(x["status"]) or x["status"] == "Unknown" else x["status"], axis=1)
    df["suggestion"] = df.apply(lambda x: generate_suggestion(x["status"]) if pd.isna(x["suggestion"]) else x["suggestion"], axis=1)

# --- Sidebar: Filter & Upload ---
st.sidebar.header("Filter, Upload & Input Data")

status_filter = st.sidebar.selectbox(
    "Filter by Land Status",
    ["All", "Healthy", "At Risk", "Degraded", "Critical"],
)

if status_filter != "All":
    df = df[df["status"] == status_filter]

# --- Upload CSV Section ---
st.sidebar.subheader("Upload New Land Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    new_data = pd.read_csv(uploaded_file)
    new_data.columns = new_data.columns.str.strip().str.lower()

    st.sidebar.write("Preview:")
    st.sidebar.dataframe(new_data.head())

    required_cols = ["soil_moisture", "vegetation_index", "temperature", "latitude", "longitude"]
    for col in required_cols:
        if col not in new_data.columns:
            st.sidebar.error(f"❌ Missing column: {col}")
            st.stop()

    if "location" not in new_data.columns:
        geolocator = Nominatim(user_agent="terrascope")
        new_data["location"] = new_data.apply(
            lambda x: geolocator.reverse((x["latitude"], x["longitude"]), language="en").address
            if pd.notna(x["latitude"]) and pd.notna(x["longitude"]) else "Unknown",
            axis=1,
        )

    new_data["status"] = new_data.apply(classify_status, axis=1)
    new_data["suggestion"] = new_data["status"].apply(generate_suggestion)

    if st.sidebar.button("Add CSV Data"):
        try:
            for _, row in new_data.iterrows():
                supabase.table("land_data").insert({
                    "location": row["location"],
                    "soil_moisture": row["soil_moisture"],
                    "vegetation_index": row["vegetation_index"],
                    "temperature": row["temperature"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "status": row["status"],
                    "suggestion": row["suggestion"],
                }).execute()
            st.sidebar.success("✅ CSV data successfully added!")
            st.cache_data.clear()
            df = load_data()
        except Exception as e:
            st.sidebar.error(f"❌ Upload failed: {e}")

# --- Manual Data Entry Section ---
st.sidebar.subheader("Or Enter Data Manually")
with st.sidebar.form("manual_input_form"):
    soil_moisture = st.number_input("Soil Moisture (%)", min_value=0.0, step=0.1)
    vegetation_index = st.number_input("Vegetation Index (NDVI)", min_value=0.0, step=0.01)
    temperature = st.number_input("Temperature (°C)", step=0.1)
    latitude = st.number_input("Latitude", format="%.6f")
    longitude = st.number_input("Longitude", format="%.6f")
    submitted = st.form_submit_button("Add Record")

    if submitted:
        geolocator = Nominatim(user_agent="terrascope")
        location_name = "Unknown"
        try:
            loc = geolocator.reverse((latitude, longitude), language="en")
            if loc:
                location_name = loc.address
        except:
            pass

        status = classify_status({
            "soil_moisture": soil_moisture,
            "vegetation_index": vegetation_index,
        })
        suggestion = generate_suggestion(status)

        try:
            supabase.table("land_data").insert({
                "location": location_name,
                "soil_moisture": soil_moisture,
                "vegetation_index": vegetation_index,
                "temperature": temperature,
                "latitude": latitude,
                "longitude": longitude,
                "status": status,
                "suggestion": suggestion,
            }).execute()
            st.sidebar.success("✅ Record added successfully!")
            st.cache_data.clear()
            df = load_data()
        except Exception as e:
            st.sidebar.error(f"❌ Failed to add record: {e}")

# --- Overview Metrics ---
st.subheader("📊 Overview Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", len(df))
col2.metric("Healthy Lands", (df["status"] == "Healthy").sum())
col3.metric("At Risk", (df["status"] == "At Risk").sum())
col4.metric("Degraded Lands", (df["status"] == "Degraded").sum())

# --- Map Visualization ---
st.subheader("🗺️ Land Health Map")
status_colors = {
    "Healthy": "green",
    "At Risk": "orange",
    "Degraded": "red",
    "Critical": "purple",
    "Unknown": "gray",
}

fig = px.scatter_mapbox(
    df,
    lat="latitude",
    lon="longitude",
    color="status",
    color_discrete_map=status_colors,
    hover_name="location",
    hover_data={
        "soil_moisture": True,
        "vegetation_index": True,
        "temperature": True,
        "suggestion": True,
    },
    zoom=4,
    height=600,
)

fig.update_layout(mapbox_style="carto-positron", legend_title="Land Health Status")
st.plotly_chart(fig, use_container_width=True)

# --- Data Table ---
st.subheader("📋 Land Data Table")
st.dataframe(df)

# --- Download Button ---
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download Current Data", csv, "land_data.csv", "text/csv")
