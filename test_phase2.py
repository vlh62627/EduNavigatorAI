import warnings
warnings.filterwarnings("ignore")

from utils.embeddings import load_vector_db, query_vector_db
from utils.geo_filter import (
    load_geo_data,
    get_all_states,
    get_education_levels,
    is_county_applicable,
    get_counties_for_level,
    filter_schools,
    get_filter_summary
)

print("=" * 55)
print("   Phase 2 Test — Data Layer & Vector DB")
print("=" * 55)

# ── Test 1: Load Dataset ───────────────────────────
print("\n--- Test 1: Load Dataset ---")
df = load_geo_data()
print(f"✅ Dataset loaded: {len(df)} schools")

# ── Test 2: All US States Dropdown ────────────────
print("\n--- Test 2: All US States ---")
states = get_all_states()
print(f"✅ Total states in dropdown: {len(states)}")
print(f"   First 5 : {states[:5]}")
print(f"   Last 5  : {states[-5:]}")

# ── Test 3: Education Levels ───────────────────────
print("\n--- Test 3: Education Levels ---")
levels = get_education_levels()
print(f"✅ Education levels: {levels}")

# ── Test 4: County Applicability Logic ────────────
print("\n--- Test 4: County Filter Logic ---")
for level in levels:
    county_needed = is_county_applicable(level)
    symbol = "✅ County filter ON " if county_needed else "🚫 County filter OFF"
    print(f"   {symbol} → {level}")

# ── Test 5: County Filter for Lower Levels ────────
print("\n--- Test 5: Counties for High School in Texas ---")
counties = get_counties_for_level(df, "Texas", "High School")
print(f"✅ Counties with High Schools in Texas: {counties}")

print("\n--- Test 5b: Counties for University in Texas ---")
counties_uni = get_counties_for_level(df, "Texas", "University")
print(f"✅ Counties for University (should be empty): {counties_uni}")

# ── Test 6: Filtering Schools ─────────────────────
print("\n--- Test 6: Filter Schools ---")

# University — state level only
uni_results = filter_schools(df, state="Texas", level="University")
print(f"\n✅ Universities in Texas (no county): {len(uni_results)} found")
for _, row in uni_results.iterrows():
    print(f"   → {row['name']} | {row['city']} | Rating: {row['rating']}")

# High School — with county
hs_results = filter_schools(
    df, state="Texas", level="High School", county="Collin"
)
print(f"\n✅ High Schools in Collin County, Texas: {len(hs_results)} found")
for _, row in hs_results.iterrows():
    print(f"   → {row['name']} | {row['city']} | Rating: {row['rating']}")

# Preschool — with county
ps_results = filter_schools(
    df, state="Texas", level="Preschool", county="Collin"
)
print(f"\n✅ Preschools in Collin County, Texas: {len(ps_results)} found")
for _, row in ps_results.iterrows():
    print(f"   → {row['name']} | {row['city']} | Rating: {row['rating']}")

# ── Test 7: Filter Summary Messages ───────────────
print("\n--- Test 7: Filter Summary Messages ---")
print(f"   {get_filter_summary('Texas', 'University')}")
print(f"   {get_filter_summary('Texas', 'High School', 'Collin')}")
print(f"   {get_filter_summary('Texas', 'Preschool')}")
print(f"   {get_filter_summary(None, None)}")

# ── Test 8: Build Vector DB ────────────────────────
print("\n--- Test 8: Build Vector DB ---")
collection = load_vector_db()

# ── Test 9: Semantic Search ────────────────────────
print("\n--- Test 9: Semantic Search ---")
queries = [
    (
        "best high school with AP courses",
        {"state": "Texas", "level": "High School"}
    ),
    (
        "affordable university with engineering programs",
        {"state": "Texas", "level": "University"}
    ),
    (
        "Montessori preschool with small class sizes",
        {"state": "Texas", "level": "Preschool"}
    ),
]

for query_text, filters in queries:
    print(f"\n🔍 Query : '{query_text}'")
    print(f"   Filter: {filters}")
    results = query_vector_db(
        collection, query_text,
        filters=filters, n_results=3
    )
    for i, (meta, dist) in enumerate(zip(
        results["metadatas"][0],
        results["distances"][0]
    )):
        score = round((1 - dist) * 100, 1)
        print(f"   #{i+1} {meta['name']} ({meta['city']}) — Match: {score}%")

print("\n" + "=" * 55)
print("✅ Phase 2 Complete! Data layer is ready.")
print("=" * 55)