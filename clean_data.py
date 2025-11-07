import pandas as pd
from supabase import create_client
import streamlit as st

# Load Supabase keys
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase = create_client(supabase_url, supabase_key)

# Fetch data
response = supabase.table("land_data").select("*").execute()
data = pd.DataFrame(response.data)

st.write("Original Data Count:", len(data))

# Drop rows with missing coordinates or empty locations
clean_data = data.dropna(subset=["latitude", "longitude"])
clean_data = clean_data[clean_data["location"].str.strip() != ""]

# Drop duplicates
clean_data = clean_data.drop_duplicates(subset=["latitude", "longitude"])

st.write("Cleaned Data Count:", len(clean_data))

# Show cleaned dataset
st.dataframe(clean_data)
