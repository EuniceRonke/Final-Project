import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client
from geopy.geocoders import Nominatim
from folium.plugins import MarkerCluster
import branca.colormap as cm

# --------------------------
# Setup
# --------------------------
st.set_page_config(page_title="TerraScope - Land Health Monitor", layout="wide")
st.title("🌍 TerraScope - Land Health Monitoring Dashboard")

st.markdown("""
TerraScope is an AI-powered land monitoring dashboard that tracks early signs of land degradation.
It analyzes soil moisture, vegetation health, and temperature, and displays the results through 
real-time charts, alerts, and an interactive map. The tool helps land managers make faster, 
data-driven decisions by highlighting unhealthy areas and showing how conditions change over time.
""")

# --------------------------
# Supabase Setup (Safe)
# --------------------------
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

# --------------------------
# Helper functions
# --------------------------
def classify_land(veg_index, soil_moisture, temp):
    if veg_index < 0.3 or soil_moisture < 20 or temp > 35:
        return "Degraded"
    elif veg_index < 0.5 or soil_moisture < 35:
        return "At Risk"
    return "Healthy"

def get_suggestion(status):
    if status == "Degraded":
        return "Recommend: Reforestation or irrigation to restore soil health."
    elif status == "At Risk":
        return "Recommend: Mulching, cover crops, or moderate irrigation."
    return "Land is healthy. Maintain current practices."

def get_color(status):
    return {"Degraded": "red", "At Risk": "orange", "Healthy": "green"}.get(status, "gray")

@st.cache_data(ttl=600)
def fetch_data():
    """Fetch data from Supabase with caching"""
    try:
        res = supabase.table("land_data").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            return pd.DataFrame()
        df = clean_data(df)
        return df
    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
        return pd.DataFrame()

def clean_data(df):
    """Clean and preprocess land dataset"""
    df = df.drop_duplicates()
    df.columns = df.columns.str.strip().str.lower()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df["vegetation_index"] = pd.to_numeric(df["vegetation_index"], errors="coerce").fillna(0.5)
    df["soil_moisture"] = pd.to_numeric(df["soil_moisture"], errors="coerce").fillna(30)
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce").fillna(25)
    df["status"] = df.apply(lambda r: classify_land(r["vegetation_index"], r["soil_moisture"], r["temperature"]), axis=1)
    df["suggestion"] = df["status"].apply(get_suggestion)
    return df

# --------------------------
# Load Data
# --------------------------
data = fetch_data()

if data.empty:
    st.warning("No land data found in Supabase.")
else:
    st.success("✅ Data fetched successfully from Supabase.")

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    status_filter = st.sidebar.multiselect(
        "Select Land Status",
        options=data["status"].unique(),
        default=list(data["status"].unique())
    )
    filtered = data[data["status"].isin(status_filter)]

    # Map
    st.subheader("🗺️ Land Health Map")

    m = folium.Map(location=[9.0820, 8.6753], zoom_start=5, tiles="cartodb positron")
    cluster = MarkerCluster().add_to(m)

    for _, row in filtered.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=7,
            color=get_color(row["status"]),
            fill=True,
            fill_color=get_color(row["status"]),
            fill_opacity=0.9,
            popup=folium.Popup(
                f"<b>Location:</b> {row.get('location', 'Unknown')}<br>"
                f"<b>Status:</b> {row['status']}<br>"
                f"<b>Suggestion:</b> {row['suggestion']}",
                max_width=250,
            ),
        ).add_to(cluster)

    # Dynamic legend
    legend_html = """
    <div style='position: fixed; bottom: 30px; left: 30px; width: 160px;
                background: white; z-index:9999; border-radius:8px;
                border:1px solid grey; padding: 10px; font-size:14px;'>
        <b>Legend</b><br>
        <i style="background:green; width:12px; height:12px; border-radius:50%; display:inline-block;"></i> Healthy<br>
        <i style="background:orange; width:12px; height:12px; border-radius:50%; display:inline-block;"></i> At Risk<br>
        <i style="background:red; width:12px; height:12px; border-radius:50%; display:inline-block;"></i> Degraded
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=900, height=500)
    st.markdown("### 📋 Land Data Table")
    st.dataframe(filtered)

# --------------------------
# Data Input Form
# --------------------------
st.markdown("---")
st.subheader("🧩 Add New Land Data")

with st.form("land_form"):
    latitude = st.number_input("Latitude", format="%.6f")
    longitude = st.number_input("Longitude", format="%.6f")
    vegetation_index = st.slider("Vegetation Index", 0.0, 1.0, 0.5)
    soil_moisture = st.number_input("Soil Moisture (%)", 0, 100, 40)
    temperature = st.number_input("Temperature (°C)", 0, 60, 28)
    submit = st.form_submit_button("Submit Data")

    if submit:
        geolocator = Nominatim(user_agent="terrascope")
        try:
            location_name = geolocator.reverse((latitude, longitude), timeout=10).address
        except:
            location_name = "Unknown Location"

        status = classify_land(vegetation_index, soil_moisture, temperature)
        suggestion = get_suggestion(status)

        insert_data = {
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "soil_moisture": soil_moisture,
            "vegetation_index": vegetation_index,
            "temperature": temperature,
            "status": status,
            "suggestion": suggestion,
        }

        try:
            supabase.table("land_data").insert(insert_data).execute()
            st.success("✅ Data successfully added!")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"❌ Failed to add data: {e}")

# --------------------------
# Footer
# --------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <img src="https://app.greenweb.org/api/v3/greencheckimage/terrascope.streamlit.app?nocache=true"
             alt="This website runs on green hosting - verified by thegreenwebfoundation.org"
             width="200px" height="95px">
        <p style='font-size: 14px; color: gray;'>
            This website runs on green hosting — verified by thegreenwebfoundation.org
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
