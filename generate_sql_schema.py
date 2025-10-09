import pandas as pd

# 1. Load a small sample (enough to infer types)
df = pd.read_csv("Delaware_Wells.csv", nrows=1000)

# 2. Helper to map pandas dtypes → PostgreSQL
def map_dtype(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "TEXT"
    elif pd.api.types.is_float_dtype(dtype):
        return "TEXT"
    elif pd.api.types.is_bool_dtype(dtype):
        return "TEXT"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TEX"
    else:
        return "TEXT"

# 3. Infer SQL column definitions
cols = [f'  "{c}" {map_dtype(df[c].dtype)}' for c in df.columns]

# 4. Add basin + geom columns
cols.append('  basin TEXT NOT NULL')
cols.append('  geom GEOGRAPHY(Point, 4326)')

# 5. Build CREATE TABLE
table_sql = "CREATE TABLE wells (\n  id BIGSERIAL PRIMARY KEY,\n" + ",\n".join(cols) + "\n);"

# 6. Add trigger to auto-populate geom
trigger_sql = """
CREATE OR REPLACE FUNCTION set_geom()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW."Latitude" IS NOT NULL AND NEW."Longitude" IS NOT NULL THEN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW."Longitude", NEW."Latitude"), 4326);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER wells_geom_trigger
BEFORE INSERT OR UPDATE ON wells
FOR EACH ROW EXECUTE PROCEDURE set_geom();

CREATE INDEX wells_geom_idx   ON wells USING GIST (geom);
CREATE INDEX wells_basin_idx  ON wells (basin);
"""

# 7. Write to file
with open("create_wells_table.sql", "w", encoding="utf-8") as f:
    f.write(table_sql + "\n" + trigger_sql)

print("✅  SQL script written to create_wells_table.sql")
