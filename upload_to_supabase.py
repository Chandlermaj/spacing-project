import pandas as pd
from supabase import create_client, Client

# --- Connect to Supabase ---
url = "https://kjaevdkcvucazcyaapry.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqYWV2ZGtjdnVjYXpjeWFhcHJ5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTkwNDgyNywiZXhwIjoyMDc1NDgwODI3fQ.J-sEleEXff1D2vLyEYogVXEqWr3OsE7bs8Uol0tVy70"
supabase: Client = create_client(url, key)

# --- Load CSV with exact casing ---
df = pd.read_csv("Delaware_Wells.csv", dtype=str)

# Don't lowercase headers — preserve as-is
df.columns = df.columns.str.strip()

# Replace invalid float/NaN values
df = df.replace([float('inf'), float('-inf')], None).where(pd.notnull(df), None)

# Add basin column
df["basin"] = "Delaware"

# Drop columns known to be missing (temporary safeguard)
if "abstract" in df.columns:
    df = df.drop(columns=["abstract"])

# --- Upload in batches ---
batch_size = 500
total_rows = len(df)

print(f"✅ Prepared {total_rows} rows and {len(df.columns)} columns for upload.")

for i in range(0, total_rows, batch_size):
    chunk = df.iloc[i:i + batch_size].to_dict(orient="records")
    try:
        response = supabase.table("wells").insert(chunk).execute()
        print(f"✅ Uploaded rows {i + 1}–{min(i + batch_size, total_rows)} | Status: {getattr(response, 'status_code', None)}")
    except Exception as e:
        print(f"⚠️ Error uploading rows {i + 1}–{i + batch_size}: {e}")

print("🎉 Upload complete.")
