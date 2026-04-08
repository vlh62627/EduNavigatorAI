# Save as debug_levels.py in root folder
import pandas as pd

df = pd.read_csv("data/nces_schools.csv", encoding="latin-1", low_memory=False)

print("LEVEL column unique values:")
print(df["LEVEL"].value_counts())

print("\nGSLO unique values (sample):")
print(df["GSLO"].value_counts().head(20))

print("\nGSHI unique values (sample):")
print(df["GSHI"].value_counts().head(20))

print("\nSample of High schools by name:")
hs = df[df["SCH_NAME"].str.contains("HIGH", case=False, na=False)]
print(hs[["SCH_NAME", "LEVEL", "GSLO", "GSHI", "SCH_TYPE_TEXT"]].head(10).to_string())

print("\nSample of Middle schools by name:")
ms = df[df["SCH_NAME"].str.contains("MIDDLE", case=False, na=False)]
print(ms[["SCH_NAME", "LEVEL", "GSLO", "GSHI"]].head(10).to_string())