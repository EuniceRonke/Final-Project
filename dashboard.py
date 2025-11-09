import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import toml
from datetime import datetime
from io import StringIO

# -----------------------------------
# Backend API URL
# -----------------------------------
BACKEND_URL = "http://127.0.0.1:8000"  # Change this when you deploy backend

# -----------------------------------
# Page Configuration
# -----------------------------------
st.set_page_config(page_title="Terrascope Dashboard", layout="wide")
st.title("🌍 Terrascope Land Health Dashboard")

# -----------------------------------
# Fetch Data Function
# -----------------------------------
@st.cache_data(ttl=60)
def fetch_data():
    try:
        res = requests.get(f"{BACKEND_URL}/data")
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data)
            if "vegetation_index" in df.columns:
                df.rename(columns={"vegetation_index": "vegetation"}, inplace=True)
            for col in ["status", "suggestion"]:
                if col not in df.columns:
                    df[col] = "Unknown"
            return df
        else:
            st.error("Failed to fetch data from backend.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = fetch_data()

# -----------------------------------
# Sidebar Controls
# -----------------------------------
st.sidebar.title("⚙️ Dashboard Controls")

# ===== Upload Section =====
with st.sidebar.expander("📤 Upload CSV Data"):
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            new_data = pd.read_csv(uploaded_file)
            st.success("File uploaded successfully.")
            st.write("Preview:")
            st.dataframe(new_data.head())
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ===== Filter Section =====
with st.sidebar.expander("🔍 Filter Data", expanded=True):
    status_filter = st.multiselect(
        "Select Land Status:",
        options=["Healthy", "At Risk", "Degraded"],
        default=["Healthy", "At Risk", "Degraded"]
    )
    filtered_df = df[df["status"].isin(status_filter)] if not df.empty else df

# ===== Manual Input Section =====
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
            if soil >= 40 and vegetation >= 0.6:
                status = "Healthy"
                suggestion = "Land is healthy. Maintain current practices."
            elif 20 <= soil < 40 or 0.4 <= vegetation < 0.6:
                status = "At Risk"
                suggestion = "Mulching, cover crops, or moderate irrigation."
            else:
                status = "Degraded"
                suggestion = "Reforestation or irrigation needed."

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
                res = requests.post(f"{BACKEND_URL}/add", json=payload)
                if res.status_code == 200:
                    st.success("Data added successfully.")
                    st.cache_data.clear()
                else:
                    st.error("Failed to upload data.")
            except Exception as e:
                st.error(f"Error uploading data: {e}")

# ===== Download Section =====
with st.sidebar.expander("📥 Download Data"):
    if not df.empty:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download Current Data as CSV",
            data=csv_data,
            file_name="land_data.csv",
            mime="text/csv"
        )
    else:
        st.info("No data to download.")

# -----------------------------------
# Main Dashboard Content
# -----------------------------------
if not df.empty:
    st.subheader("📊 Land Health Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", len(df))
    col2.metric("Healthy", len(df[df["status"] == "Healthy"]))
    col3.metric("At Risk", len(df[df["status"] == "At Risk"]))
    col4.metric("Degraded", len(df[df["status"] == "Degraded"]))

    # ===== Table Display =====
    st.subheader("📋 Land Data Table")
    st.dataframe(filtered_df, use_container_width=True)

    # ===== Map Visualization =====
    st.subheader("🗺️ Land Health Map")

    fig = px.scatter_mapbox(
        filtered_df,
        lat="latitude",
        lon="longitude",
        color="status",
        hover_name="location",
        hover_data=["soil_moisture", "vegetation", "temperature", "suggestion"],
        color_discrete_map={
            "Healthy": "green",
            "At Risk": "orange",
            "Degraded": "red"
        },
        zoom=4,
        height=600
    )

    fig.update_layout(
        mapbox_style="open-street-map",  # English map
        legend_title="Land Health Status",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data available yet. Add or upload some to begin.")
