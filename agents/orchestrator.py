import os
import logging
import warnings
warnings.filterwarnings("ignore")
logging.getLogger("chromadb").setLevel(logging.ERROR)

from dotenv import load_dotenv
from agents.librarian_agent      import librarian_agent
from agents.researcher_agent     import researcher_agent
from agents.doc_specialist_agent import doc_specialist_agent
from utils.geo_filter            import has_local_data
from utils.college_scorecard_api import fetch_universities
from utils.nces_api              import fetch_k12_schools
from utils.embeddings            import cache_api_schools, is_cached

load_dotenv()

MIN_LOCAL_RESULTS = 2
K12_LEVELS  = ["Preschool", "Elementary", "Middle School", "High School"]
UNI_LEVELS  = ["University", "Community College", "Medical School"]


def orchestrator(
    collection,
    query,
    state        = None,
    level        = None,
    county       = None,
    city         = None,
    n_results    = 20,
    generate_pdf = False,
    school_name  = None,
    df           = None
):
    print("\n" + "=" * 55)
    print("🎯 ORCHESTRATOR ACTIVATED")
    print(f"   Query  : {query}")
    print(f"   State  : {state} | Level: {level}")
    print(f"   County : {county} | City: {city}")
    print("=" * 55)

    response = {
        "source":          None,
        "schools":         [],
        "api_schools":     [],
        "local_summary":   "",
        "web_summary":     "",
        "web_sources":     [],
        "pdf_result":      None,
        "query":           query,
        "filters_used":    {
            "state": state, "level": level,
            "county": county, "city": city
        },
        "agents_called":   [],
        "has_local_data":  False,
        "from_cache":      False
    }

    # Build ChromaDB filters
    filters = {}
    if state:  filters["state"] = state
    if level:  filters["level"] = level
    if county and county not in ["All Counties", "Select County"]:
        filters["county"] = county

    # ── Check local CSV data ──────────────────────
    local_data_exists = False
    if df is not None and state and level:
        local_data_exists = has_local_data(df, state, level)
    response["has_local_data"] = local_data_exists

    # ── For K-12 always use NCES database ─────────
    # Never use cache for K-12 — cache has no district
    # filtering capability, always fetch fresh from NCES
    if level in K12_LEVELS:
        local_data_exists = False
        cache_hit         = False
        print(f"   ℹ️ K-12 — fetching from NCES database.")
    else:
        # ── Check ChromaDB cache (universities only) ─
        cache_hit = False
        if not local_data_exists and state and level:
            cache_hit = is_cached(collection, state, level)
            if cache_hit:
                print(f"\n⚡ Cache HIT for {level} in {state}.")
                response["from_cache"] = True

    # ══════════════════════════════════════════════
    # STEP 1 — Librarian Agent (local CSV or cache)
    # ══════════════════════════════════════════════
    if local_data_exists or cache_hit:
        source_label = "local CSV" if local_data_exists else "cache"
        print(f"\n📋 Step 1: Librarian Agent ({source_label})...")
        librarian_result = librarian_agent(
            collection = collection,
            query      = query,
            filters    = filters,
            n_results  = 20
        )
        response["agents_called"].append("Librarian")
        response["schools"]       = librarian_result["schools"]
        response["local_summary"] = librarian_result["summary"]
        local_count               = len(librarian_result["schools"])
        print(f"   📊 Results: {local_count}")
    else:
        local_count = 0
        print(f"\n   ℹ️ No local/cached data for {level} in {state}.")

    # ══════════════════════════════════════════════
    # STEP 2 — Government API / NCES Search
    # ══════════════════════════════════════════════
    api_schools = []

    if not local_data_exists and not cache_hit and state and level:
        if level in UNI_LEVELS:
            print(f"\n📋 Step 2: College Scorecard API...")
            api_schools = fetch_universities(
                state=state, level=level, per_page=20
            )
            response["agents_called"].append("CollegeScorecard")

        elif level in K12_LEVELS:
            print(f"\n📋 Step 2: NCES K-12 Search...")
            print(f"   DEBUG county='{county}' city='{city}'")
            api_schools = fetch_k12_schools(
                state  = state,
                level  = level,
                county = county,
                city   = city,
                limit  = 20
            )
            response["agents_called"].append("NCES_API")

        # Cache results in ChromaDB
        if api_schools:
            print(f"   💾 Caching {len(api_schools)} schools...")
            cache_api_schools(collection, api_schools, source="api")
            response["source"]      = "api"
            response["api_schools"] = api_schools
        else:
            print("   ⚠️ API returned nothing. Falling back to web.")

    # ══════════════════════════════════════════════
    # STEP 3 — Researcher Agent (web search)
    # ══════════════════════════════════════════════
    specific_keywords = [
        "ut austin", "harvard", "stanford", "mit",
        "yale", "princeton", "texas tech", "baylor",
        "rice university", "tcu", "duke", "vanderbilt",
        "georgetown", "notre dame", "emory", "tulane",
        "ohio state", "penn state", "purdue",
        "georgia tech", "virginia tech", "arizona state"
    ]
    query_lower        = query.lower()
    is_specific_school = any(
        kw in query_lower for kw in specific_keywords
    )
    is_auto_query      = query.startswith("Provide ")

    needs_web = (
        (not local_data_exists and
         not cache_hit and
         not api_schools)     or
        is_specific_school
        # Removed is_auto_query — NCES results
        # are sufficient for K-12 auto queries
    )

    if needs_web:
        reason = (
            "specific school"  if is_specific_school else
            "auto query"       if is_auto_query else
            "no API results"
        )
        print(f"\n📋 Step 3: Researcher Agent ({reason})...")
        researcher_result = researcher_agent(
            query     = query,
            state     = state,
            level     = level,
            n_results = 5
        )
        response["agents_called"].append("Researcher")
        response["web_summary"] = researcher_result["summary"]
        response["web_sources"] = researcher_result["sources"]
        response["source"]      = (
            "both" if (local_count > 0 or api_schools)
            else "web"
        )
    else:
        if local_count > 0 and not cache_hit:
            response["source"] = "local"
        elif cache_hit:
            response["source"] = "cache"

    # ══════════════════════════════════════════════
    # STEP 4 — Doc Specialist Agent (PDF)
    # ══════════════════════════════════════════════
    if generate_pdf and school_name:
        print(f"\n📋 Step 4: Doc Specialist for '{school_name}'...")
        pdf_result = doc_specialist_agent(
            school_name   = school_name,
            level         = level or "University",
            state         = state or "Texas",
            extra_context = query
        )
        response["agents_called"].append("DocSpecialist")
        response["pdf_result"] = pdf_result
    else:
        print("\n   ℹ️ PDF not requested.")

    print("\n" + "=" * 55)
    print("✅ ORCHESTRATOR COMPLETE")
    print(f"   Agents : {', '.join(response['agents_called'])}")
    print(f"   Source : {response['source']}")
    print(f"   Local  : {len(response['schools'])}")
    print(f"   API    : {len(response['api_schools'])}")
    print("=" * 55)

    return response