import pandas as pd
from utils.geo_filter import get_counties_for_level

df     = pd.read_csv('data/schools.csv')
result = get_counties_for_level(df, 'Texas', 'High School')
print(f'Counties found: {len(result)}')
print(result[:5])