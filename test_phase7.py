import warnings
import logging
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from utils.college_scorecard_api import fetch_universities
from utils.nces_api              import fetch_k12_schools

print("=" * 55)
print("   Phase 7 Test — Government APIs")
print("=" * 55)

# Test 1: Universities in Alaska
print("\n--- Test 1: Universities in Alaska ---")
schools = fetch_universities("Alaska", "University", per_page=5)
for s in schools[:3]:
    print(f"   → {s['name']} | {s['city']} | "
          f"Tuition: ${s['tuition_min']:,}")

# Test 2: Medical Schools in California
print("\n--- Test 2: Medical Schools in California ---")
med = fetch_universities("California", "Medical School", per_page=20)
for s in med[:3]:
    print(f"   → {s['name']} | {s['city']}")

# Test 3: Community Colleges in Texas
print("\n--- Test 3: Community Colleges in Texas ---")
cc = fetch_universities("Texas", "Community College", per_page=5)
for s in cc[:3]:
    print(f"   → {s['name']} | {s['city']} | "
          f"Tuition: ${s['tuition_min']:,}")

# Test 4: Elementary Schools in Alaska
print("\n--- Test 4: Elementary Schools in Alaska ---")
k12 = fetch_k12_schools("Alaska", "Elementary", limit=5)
for s in k12[:3]:
    print(f"   → {s['name']} | {s['city']} | "
          f"Students: {s['student_count']}")

# Test 5: High Schools in Ohio
print("\n--- Test 5: High Schools in Ohio ---")
hs = fetch_k12_schools("Ohio", "High School", limit=5)
for s in hs[:3]:
    print(f"   → {s['name']} | {s['city']}")

print("\n" + "=" * 55)
print("✅ Phase 7 API Tests Complete!")
print("=" * 55)