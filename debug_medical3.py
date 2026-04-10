import requests, os
from dotenv import load_dotenv
load_dotenv()

resp = requests.get(
    "https://api.data.gov/ed/collegescorecard/v1/schools",
    params={
        "api_key":      os.getenv("COLLEGE_SCORECARD_API_KEY"),
        "school.state": "TX",
        "school.name":  "southwestern",
        "fields":       "school.name,school.city,id,school.degrees_awarded.predominant",
        "per_page":     10
    },
    timeout=15
)
data = resp.json()
print("UT Southwestern in API:")
for r in data.get("results", []):
    print(f"  Name      : {r.get('school.name')}")
    print(f"  City      : {r.get('school.city')}")
    print(f"  Predominant: {r.get('school.degrees_awarded.predominant')}")
    print()