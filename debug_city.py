# debug_filter.py
import pandas as pd

df = pd.read_csv('data/k12_schools.csv', low_memory=False)

for col in ["state", "level", "district", "county", "city", "name"]:
    if col in df.columns:
        df[col] = df[col].fillna("").astype(str).replace({"nan": "", "None": ""})

filtered = df[(df['state'] == 'Texas') & (df['level'] == 'High School')]
print(f"After state+level filter: {len(filtered)} schools")

county = "FRISCO ISD"
dist_mask = (
    filtered["district"].str.contains(county, case=False, na=False) |
    filtered["county"].str.contains(county, case=False, na=False)
)
result = filtered[dist_mask]
print(f"After district filter '{county}': {len(result)} schools")
print(result[['name','district','city']].head(5).to_string())