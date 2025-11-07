import streamlit as st
from supabase import create_client, Client

# Load secrets
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

# Initialize Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Try fetching data
try:
    response = supabase.table("land_data").select("*").execute()
    st.write("✅ Connection successful!")
    st.write(response.data)
except Exception as e:
    st.error(f"❌ Error connecting to Supabase: {e}")
