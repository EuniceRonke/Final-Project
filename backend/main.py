from fastapi import FastAPI
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
from supabase import create_client, Client
import os
import toml
from dotenv import load_dotenv

# === Debug print at startup ===
print("Terrascope API starting...")

# === Load .env first ===
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# === Fallback to secrets.toml in project root ===
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
secrets_path = os.path.join(PROJECT_ROOT, "secrets.toml")

if os.path.exists(secrets_path):
    with open(secrets_path, "r") as f:
        secrets = toml.load(f)
    SUPABASE_URL = SUPABASE_URL or secrets.get("SUPABASE_URL") or secrets.get("supabase", {}).get("url")
    SUPABASE_KEY = SUPABASE_KEY or secrets.get("SUPABASE_SERVICE_KEY") or secrets.get("supabase", {}).get("key")
else:
    print(f"⚠️ secrets.toml not found at {secrets_path}, using .env only.")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY, continuing in debug mode (read-only)")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client created successfully")
    except Exception as e:
        print("❌ Failed to create Supabase client:", e)
        supabase = None

# === Safe import of carbon utils ===
try:
    from .utils.carbon import estimate_carbon_emission
    print("✅ Carbon utils loaded")
except Exception as e:
    print("⚠️ Failed to import carbon utils:", e)
    estimate_carbon_emission = None

# === FastAPI setup ===
app = FastAPI(title="Terrascope API", version="1.0")

# === Pydantic model ===
class LandData(BaseModel):
    location: str = Field(..., example="Field A")
    soil_moisture: float = Field(..., example=0.35)
    vegetation_index: float = Field(..., example=0.78)
    temperature: float = Field(..., example=25.4)
    latitude: float = Field(..., example=12.3456)
    longitude: float = Field(..., example=98.7654)

# === Routes ===
@app.get("/")
def read_root():
    return {"message": "Welcome to Terrascope API"}

@app.get("/data")
def get_all_data():
    if not supabase:
        return {"detail": "Supabase client not configured"}
    try:
        response = supabase.table("land_data").select("*").execute()
        return response.data
    except Exception as e:
        return {"detail": str(e)}

@app.post("/add")
def add_data(record: LandData):
    if not supabase:
        return {"detail": "Supabase client not configured"}
    if not estimate_carbon_emission:
        return {"detail": "Carbon estimation function not available"}

    try:
        sustainability_index = round(
            (record.soil_moisture * 0.4 + record.vegetation_index * 0.6) * 100, 2
        )

        result = estimate_carbon_emission(record.soil_moisture, record.vegetation_index)
        carbon_estimate = result.get("estimated_emission", 0)
        status = result.get("status", "unknown")
        suggestion = result.get("suggestion", "")

        beacon_id = str(uuid4())
        data = {
            "location": record.location,
            "soil_moisture": record.soil_moisture,
            "vegetation_index": record.vegetation_index,
            "temperature": record.temperature,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "beacon_id": beacon_id,
            "sustainability_index": sustainability_index,
            "carbon_estimate": carbon_estimate,
            "status": status,
            "suggestion": suggestion,
            "timestamp": datetime.utcnow().isoformat(),
        }

        supabase.table("land_data").insert(data).execute()
        return {"message": "Record added successfully", "data": data}
    except Exception as e:
        return {"detail": str(e)}

# === Test endpoint to confirm server runs ===
@app.get("/ping")
def ping():
    return {"status": "ok"}
