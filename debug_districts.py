import pandas as pd

df = pd.read_csv('data/k12_schools.csv', low_memory=False)

states = ["Texas", "California", "New York", "Ohio", "Alabama", "Florida"]

for state in states:
    print(f"\n=== {state} Sample Districts ===")
    districts = (
        df[df['state'] == state]['district']
        .dropna()
        .unique()[:8]
    )
    for d in districts:
        print(f"  {d}")