import requests
import os
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv(dotenv_path=os.path.join("backend", ".env"))

SUPABASE_URL = os.getenv("MY_SUPABASE_URL")
SERVICE_KEY = os.getenv("MY_SUPABASE_SERVICE_KEY")

GET_DATA_URL = f"{SUPABASE_URL}/functions/v1/terrascope/data"

HEADERS = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json"
}

# Fetch data
response = requests.get(GET_DATA_URL, headers=HEADERS)

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)
    print(f"\n✅ Fetched {len(df)} records from Supabase.\n")
    print(df.head(10))  # Show first 10 rows
else:
    print(f"\n❌ Failed to fetch data. Status code: {response.status_code}")
    print("Response:", response.text)
