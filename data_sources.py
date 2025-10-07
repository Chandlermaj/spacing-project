import pandas as pd

# Direct-download link for your file
drive_url = "https://drive.google.com/uc?export=download&id=1LasAW4-Ej8OJ5UGwpNev24pAoOSo9nP5"

# Read the CSV
df = pd.read_csv(drive_url)

# Show first few rows
print(df.head())
